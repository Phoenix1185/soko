# soko browser tool: playwright-driven, quattro decides selectors by reading the DOM
import json,os
os.makedirs('/home/ubuntu/soko/work',exist_ok=True)
from playwright.sync_api import sync_playwright

def run_flow(steps,shots_prefix='shot'):
    """steps: list of dicts from JSON:
       {'goto':url} {'fill':sel,'text':v} {'click':sel} {'select':sel,'value':v}
       {'check':sel} {'press':sel_or_None,'key':'Enter'} {'wait':ms}
       {'read':sel} {'screenshot':name} {'solve_invisible':None} (waits for token by idle time)
    """
    log=[];reads=[]
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-blink-features=AutomationControlled'])
        ctx=b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',viewport={'width':1366,'height':900},locale='en-US')
        pg=ctx.new_page()
        for i,st in enumerate(steps,1):
            try:
                if 'goto' in st:
                    pg.goto(st['goto'],wait_until='domcontentloaded',timeout=45000);pg.wait_for_timeout(1500)
                    log.append(f'[{i}] goto {st["goto"]} -> title: {pg.title()}')
                elif 'fill' in st:
                    pg.fill(st['fill'],st.get('text',''),timeout=10000);log.append(f'[{i}] filled {st["fill"]}')
                elif 'click' in st:
                    pg.click(st['click'],timeout=10000);pg.wait_for_timeout(1200);log.append(f'[{i}] clicked {st["click"]}')
                elif 'select' in st:
                    pg.select_option(st['select'],st.get('value'),timeout=10000);log.append(f'[{i}] selected {st["select"]}')
                elif 'check' in st:
                    pg.check(st['check'],timeout=10000);log.append(f'[{i}] checked {st["check"]}')
                elif 'press' in st:
                    pg.press(st.get('press') or 'body',st.get('key','Enter'));log.append(f'[{i}] pressed {st.get("key")}')
                elif 'wait' in st:
                    pg.wait_for_timeout(st['wait']);log.append(f'[{i}] waited {st["wait"]}ms')
                elif 'read' in st:
                    v=pg.evaluate('(sel)=>{const el=document.querySelector(sel);return el?(el.innerText||el.value||""):"(not found: "+sel+")"}',st['read']);reads.append(v[:500]);log.append(f'[{i}] read {st["read"]}: {v[:120]}')
                elif 'screenshot' in st:
                    path=f'/home/ubuntu/soko/work/{shots_prefix}-{i}.png';pg.screenshot(path=path);log.append(f'[{i}] shot {path}')
                elif 'solve_invisible' in st:
                    pg.wait_for_timeout(3500);log.append(f'[{i}] idle 3.5s for invisible captcha token')
            except Exception as e:
                log.append(f'[{i}] ERROR {type(e).__name__}: {str(e)[:150]}')
        try:pg.screenshot(path='/home/ubuntu/soko/work/final.png')
        except Exception:pass
        b.close()
    return chr(10).join(log),reads

if __name__=='__main__':
    steps=json.load(open('/home/ubuntu/soko/work/flow.json'))
    log,reads=run_flow(steps)
    print(log)
    if reads:print('READS:',reads)
