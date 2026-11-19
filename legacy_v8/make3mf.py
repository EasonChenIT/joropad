import numpy as np, zipfile
names = {"tile_top_0":"上壳-左前","tile_top_1":"上壳-右前","tile_top_2":"上壳-左后","tile_top_3":"上壳-右后",
         "tile_cover_0":"底盖-左前","tile_cover_1":"底盖-右前","tile_cover_2":"底盖-左后","tile_cover_3":"底盖-右后"}
def load(p):
    d=open(p,'rb').read(); n=int(np.frombuffer(d[80:84],'<u4')[0])
    v=np.frombuffer(d[84:],dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')],count=n)['v'].reshape(-1,3)
    u,inv=np.unique(np.round(v,4),axis=0,return_inverse=True); return u,inv.reshape(-1,3)
objs=[];items=[];x=0
for i,(k,nm) in enumerate(names.items(),1):
    V,F=load(k+'.stl'); V=V-V.min(0)
    vs="".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a,b,c in V)
    ts="".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in F)
    objs.append(f'<object id="{i}" name="{nm}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
    items.append(f'<item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {x:.1f} 0 0" printable="1"/>'); x+=V[:,0].max()+10
    print(nm, np.round(V.max(0),1))
model=('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="zh-CN" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
 '<metadata name="Title">Joro + Magic Trackpad 笔记本式主板 v8</metadata><resources>'+"".join(objs)+'</resources><build>'+"".join(items)+'</build></model>')
with zipfile.ZipFile('joro_trackpad_deck_v8.3mf','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model',model)
