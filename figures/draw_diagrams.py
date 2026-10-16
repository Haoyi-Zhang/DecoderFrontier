"""Vector drawing primitives; copied into each independent project generator."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

def obstruction(out):
    d=Drawing((-4.2,-2.4,4.2,2.4))
    d.box('r',0,0,1.15,.65,'$0000$')
    entries=[('a',-3,0,'1000','00','e','w'),
             ('b',0,1.65,'0100','01','s','n'),
             ('c',3,0,'0010','10','w','e'),
             ('d',0,-1.65,'0001','11','n','s')]
    for name,x,y,word,message,side,target in entries:
        d.box(name,x,y,1.65,.95,'$'+word+'$\n$('+message+')$')
        d.edge(name,'r',sa=side,sb=target)
    d.save(out,'obstruction')


def pipeline(out):
    d=Drawing((-.5,0,9.1,8.8))
    for name,x,y,label in [
        ('enc',1.75,8,'encoder\nassignment'),
        ('rows',1.75,6.25,'source sets and\nlegal row lists'),
        ('core',6.3,6.25,'semantic\nobstruction'),
        ('reject',6.3,4.5,'checked\ninfeasible'),
        ('cnf',1.75,4.5,'relational SOP\nCNF at bound $p$'),
        ('pair',1.75,2.75,'$p$-product circuit\nand $(p-1)$ tree'),
        ('checker',6.3,2.75,'independent\ncertificate checker'),
        ('frontier',6.3,1,'$M(a)$ and\nPareto front')]:
        d.box(name,x,y,3.25,.95,label)
    for a,b in [('enc','rows'),('core','reject'),('rows','cnf'),
                ('cnf','pair'),('checker','frontier')]:d.edge(a,b)
    d.edge('rows','core',sa='e',sb='w')
    d.text(4.02,6.65,'empty row',7.5)
    d.text(.12,5.38,'nonempty',7.5,ha='left')
    d.edge('pair','checker',sa='e',sb='w')
    d.arrow(d.point('reject','e'),d.point('frontier','e'),dashed=True,
            via=[(8.6,4.5),(8.6,1)])
    d.save(out,'pipeline')


def frontier_rows():
    import json
    root=Path(__file__).resolve().parents[1]/'results'
    result={}
    for case in ('B05','B06'):
        data=json.loads((root/(case+'.json')).read_text(encoding='utf-8'))
        rows=[(x['error'],x['gates']) for x in data['frontier']]
        if any(type(a) is not int or type(b) is not int for a,b in rows):
            raise ValueError('non-integer frontier coordinates')
        result[case]=rows
    if result!={'B05':[(0,8),(1,6)],'B06':[(0,9),(1,6)]}:
        raise ValueError('retained frontier changed; update the manuscript and drawing together')
    return result


def frontiers(out):
    rows=frontier_rows()
    fig=plt.figure(figsize=(3.5,4.55/2.54))
    ax=fig.add_axes([.16,.29,.81,.66])
    for case,label,style,marker in [
        ('B05','B05: repetition','-','o'),
        ('B06','B06: no adjacent ones','--','^')]:
        x,y=zip(*rows[case])
        ax.plot(x,y,color='black',linestyle=style,marker=marker,
                linewidth=.7,markersize=5,markerfacecolor='white',
                markeredgewidth=.7,label=label)
    ax.set(xlim=(-.12,1.12),ylim=(5.5,10.2),
           xlabel='Maximum decoded errors $A$',ylabel='Counted sites $G$')
    ax.set_xticks([0,1]);ax.set_yticks([6,7,8,9,10])
    ax.grid(color='.82',linestyle=':',linewidth=.45)
    ax.tick_params(length=3,width=.55)
    for spine in ax.spines.values():spine.set_linewidth(.55)
    ax.legend(loc='upper right',frameon=False,fontsize=8,
              handlelength=2,borderaxespad=.35,labelspacing=.35)
    fig.savefig(out/'frontiers.pdf',metadata={'Creator':'Python Matplotlib',
                'Producer':None,'CreationDate':None,'ModDate':None})
    plt.close(fig)


def figures(out,only_frontiers=False):
    if not only_frontiers:obstruction(out);pipeline(out)
    frontiers(out)


def check():
    import itertools,tempfile
    words=['1000','0100','0010','0001']
    messages=list(itertools.product((0,1),repeat=2))
    if not all(sum(a!=b for a,b in zip(w,'0000'))==1 for w in words):
        raise ValueError('obstruction arrows are not radius-one transitions')
    if any(all(sum(a!=b for a,b in zip(x,z))<=1 for x in messages) for z in messages):
        raise ValueError('illustrated radius-one output-ball intersection is nonempty')
    with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
        for out in (Path(a),Path(b)):figures(out)
        for name in ('obstruction','pipeline','frontiers'):
            if (Path(a)/(name+'.pdf')).read_bytes()!=(Path(b)/(name+'.pdf')).read_bytes():
                raise ValueError('nondeterministic direct-vector export: '+name)
    print('Three direct-vector exports: retained frontiers, obstruction geometry, label bounds and fresh-export identity passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Draw retained total-decoder figures directly, without TeX or PGF.')
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--only-frontiers',action='store_true')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:check()
    else:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        figures(args.output_dir,args.only_frontiers)

