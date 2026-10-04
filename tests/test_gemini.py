import json
import pytest
from bridge.analysis import AnalysisError, check_provider_response, SCHEMA
from conftest import post

class Response:
    def __init__(self, payload, status=200):
        self.payload=payload;self.status_code=status
    def json(self):return self.payload

def result(text):
    return {'source_language':'English','summary':'Envía las notas el viernes.',
            'actions':[{'title':'Enviar las notas','source_quote':text,'conditions':'',
                        'steps': [], 'location': None, 'deadline_text':'El viernes'}],
            'missing_information':['La fecha exacta no está indicada.'],'words':[]}

def test_gemini_custom_text_and_consent(app,client,monkeypatch):
    app.config.update(AI_MODE='gemini',GEMINI_API_KEY='test-private-value',GEMINI_MODEL='gemini-2.5-flash',OPENAI_API_KEY='')
    text='Please send the notes on Friday.'
    def fake(url,**kwargs):
        assert url=='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        assert 'test-private-value' not in url
        assert kwargs['headers']['x-goog-api-key']=='test-private-value'
        data=kwargs['json']
        assert data['generationConfig']['responseJsonSchema']==SCHEMA
        assert json.loads(data['contents'][0]['parts'][0]['text'])['document']==text
        return Response({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(result(text))}]}}]})
    monkeypatch.setattr('bridge.analysis.requests.post',fake)
    data={'text':text,'language':'es','input_language':'en'}
    assert post(client,'/api/analyze',data).status_code==400
    data['consent']=True
    r=post(client,'/api/analyze',data)
    assert r.status_code==200 and r.json['result']['summary']==result(text)['summary']

@pytest.mark.parametrize('payload',[
    {'promptFeedback':{'blockReason':'SAFETY'}},
    {'candidates':[{'finishReason':'MAX_TOKENS'}]},
    {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'not json'}]}}]},
])
def test_gemini_incomplete_or_invalid_output(app,client,monkeypatch,payload):
    app.config.update(AI_MODE='gemini',GEMINI_API_KEY='mock',GEMINI_MODEL='gemini-2.5-flash')
    monkeypatch.setattr('bridge.analysis.requests.post',lambda *a,**k:Response(payload))
    r=post(client,'/api/analyze',{'text':'Please send the notes.','language':'en','consent':True})
    assert r.status_code==422

@pytest.mark.parametrize('status,error,expected',[
    (400,{'details':[{'reason':'API_KEY_INVALID'}]},'key was rejected'),
    (403,{},'access denied'),
    (404,{},'model not found'),
    (429,{},'quota limit'),
    (503,{},'temporarily unavailable'),
])
def test_provider_diagnostics_do_not_leak_keys(status,error,expected):
    error['message']='private-key-and-document-content'
    with pytest.raises(AnalysisError) as exc:
        check_provider_response(Response({'error':error},status),'Gemini')
    assert expected in str(exc.value)
    assert 'private-key' not in str(exc.value)

def test_openai_credit_diagnostic():
    with pytest.raises(AnalysisError,match='credits/quota are exhausted'):
        check_provider_response(Response({'error':{'code':'credit_balance_exhausted'}},429),'OpenAI')
