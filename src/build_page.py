import json,sys
d=open('data.json').read(); L=json.load(open('leagues.json'))
html=open('style.part').read()+open('markup.part').read()+'\n'+open('chat.part').read()
html=html.replace('__DATA__',d,1).replace('__LEAGUES__',json.dumps(L,ensure_ascii=False,separators=(',',':')),1)
open('index.html','w').write(html)
open('local.html','w').write('<meta charset="utf-8">'+html)
print(len(html.encode())//1024,'KB')
