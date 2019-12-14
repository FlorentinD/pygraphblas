from graphviz import Digraph, Source
from pygraphblas import Matrix, Vector

def _str(s, label_width=5):
    return str(s)[:label_width]

def draw_vector(V, name='', rankdir='LR', ioff=0, joff=0):
    g = Digraph(name)
    g.attr(rankdir=rankdir, ranksep='1')
    for i, v in V:
        g.node(str(i+ioff), label='%s:%s' % (str(i), str(v)))
    return g

def draw_graph(M, name='', rankdir='LR', show_weight=True, label_vector=None, size_vector=None, ioff=0, joff=0):
    g = Digraph(name)
    g.attr(rankdir=rankdir, ranksep='1')
    for i, j, v in M:
        size = _str(size_vector[i]) if size_vector else '1.0'
        ilabel = _str(label_vector[i]) if label_vector else str(i)
        jlabel = _str(label_vector[j]) if label_vector else str(j)
        vlabel = _str(v) if show_weight else None
        
        g.node(str(i+ioff), width=size, height=size, label=ilabel)
        g.node(str(j+joff), width=size, height=jlabel)
        g.edge(str(i+ioff), str(j+joff), label=vlabel)
    return g

def draw_layers(M, name='', rankdir='LR'):
    g = Digraph(name)
    g.attr(rankdir=rankdir, ranksep='1')    
    for l, m in enumerate(M):
        with g.subgraph() as s:
            s.attr(rank='same', rankdir='LR')            
            for i in range(m.nrows):
                si = (l * m.nrows) + i
                s.node(str(si), label=_str(i), width='0.5')
                if i < m.nrows-1:
                    ni = si +1
                    s.edge(str(si), str(ni), style='invis')
                    
    with g.subgraph() as s:
        s.attr(rank='same', rankdir='LR')            
        for j in range(M[-1].nrows):
            sj = (len(M) * m.nrows) + j
            s.node(str(sj), label=_str(j), width='0.5')
            if j < M[-1].nrows-1:
                nj = sj +1
                s.edge(str(sj), str(nj), style='invis')

    for l, m in enumerate(M):
        for i, j, _ in m:
            si = (l * m.nrows) + i
            sj = ((l + 1) * m.nrows) + j
            g.edge(str(si), str(sj))
    return g

def draw(obj, name='', **kws):
    if isinstance(obj, Matrix):
        return draw_graph(obj, name, **kws)
    if isinstance(obj, Vector):
        return draw_vector(obj, name, **kws)

def draw_op(left, op, right, result):
    ioff = 0
    joff = 0
    def draw(obj, name='', **kws):
        nonlocal ioff, joff
        if isinstance(obj, Matrix):
            ioff += obj.nrows
            joff += obj.ncols
            return draw_graph(obj, name=name, ioff=ioff, joff=joff)
        if isinstance(obj, Vector):
            ioff += obj.size
            joff += obj.size
            return draw_vector(obj, name=name, ioff=ioff, joff=joff)

    g = Digraph()
    g.subgraph(draw(left, name='cluster_left'))
    g.node(op, width='0.5')
    g.subgraph(draw(right, name='cluster_right'))
    g.node('=', width='0.5')
    g.subgraph(draw(result, name='cluster_result'))
    return g
