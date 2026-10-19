import importlib
import io
import sys
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from app.core import normalize, search, extract_pdf


def make_pdf(pages):
    stream=io.BytesIO();pdf=canvas.Canvas(stream)
    for text in pages:
        pdf.drawString(50,750,text);pdf.showPage()
    pdf.save();return stream.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('RESEARCHDESK_DATA',str(tmp_path))
    for key in ('LLM_API_KEY','LLM_BASE_URL','LLM_MODEL'):monkeypatch.delenv(key,raising=False)
    sys.modules.pop('app.main',None)
    module=importlib.import_module('app.main')
    with TestClient(module.app) as client:yield client


def test_document_lifecycle(client):
    content=make_pdf(['Solar panels generate electricity.','Wind turbines supply renewable energy.'])
    r=client.post('/api/documents?name=report.pdf',content=content);assert r.status_code==200
    doc=r.json()['id'];assert r.json()['pages']==2
    assert client.post('/api/documents?name=copy.pdf',content=content).json()['duplicate']
    assert len(client.get('/api/documents').json())==1
    result=client.post('/api/search',json={'question':'wind turbines'}).json()
    assert result['sources'][0]['page']==2
    assert result['sources'][0]['document_id']==doc
    assert client.get(f'/api/documents/{doc}/pdf').content==content
    assert len(client.get('/api/history').json())==1
    client.delete('/api/documents/'+doc)
    assert client.get('/api/documents').json()==[]
    assert client.get('/api/history').json()==[]
    assert client.get(f'/api/documents/{doc}/pdf').status_code==404


def test_invalid_and_blank_pdf(client):
    assert client.post('/api/documents?name=bad.pdf',content=b'not pdf').status_code==400
    assert client.post('/api/documents?name=bad.exe',content=b'%PDF-').status_code==400
    assert client.post('/api/documents?name=scan.pdf',content=make_pdf([''])).status_code==400


def test_filter_and_no_evidence(client):
    a=client.post('/api/documents?name=a.pdf',content=make_pdf(['Solar battery storage.'])).json()['id']
    client.post('/api/documents?name=b.pdf',content=make_pdf(['Wind turbine engineering.']))
    assert not client.post('/api/search',json={'question':'turbine','document_id':a}).json()['sources']
    assert not client.post('/api/search',json={'question':'penguins'}).json()['sources']
    assert client.post('/api/search',json={'question':'  '}).status_code==400


def test_arabic_normalization():
    hits=search([{'text':'إنتاج الطاقة الشمسية في مصر','page':1}], 'انتاج الطاقة')
    assert hits and normalize('إِنْتَاج')=='انتاج'


def test_browser_origin_guard(client):
    r=client.post('/api/search',json={'question':'solar'},headers={'Origin':'https://evil.example'})
    assert r.status_code==403
    assert client.get('/',headers={'Host':'evil.example'}).status_code==400


def test_generation_not_configured(client):
    client.post('/api/documents?name=a.pdf',content=make_pdf(['Solar energy is renewable.']))
    assert not client.get('/api/status').json()['generation_available']
    assert client.post('/api/search',json={'question':'solar','generate':True}).status_code==400


def test_generation_citation_validation(client,monkeypatch):
    import app.main as main
    for k,v in {'LLM_API_KEY':'test-key','LLM_BASE_URL':'https://provider.example/v1','LLM_MODEL':'test'}.items():monkeypatch.setenv(k,v)
    class Fake:
        answer='Solar energy [1].'
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,*args,**kwargs):return self
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':self.answer}}]}
    monkeypatch.setattr(main.httpx,'AsyncClient',lambda **kwargs:Fake())
    client.post('/api/documents?name=a.pdf',content=make_pdf(['Solar energy is renewable.']))
    assert client.post('/api/search',json={'question':'solar','generate':True}).json()['mode']=='generated'
    Fake.answer='Made up [999].'
    assert client.post('/api/search',json={'question':'solar','generate':True}).json()['mode']=='excerpts'


def test_static_assets(client):
    assert client.get('/').status_code==200
    for path in ('app.js','style.css'):assert client.get('/static/'+path).status_code==200
    assert 'frame-ancestors' in client.get('/').headers['content-security-policy']
