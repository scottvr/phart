import os
import sys
from pprint import pp
import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

class Leaf:
    count = 0
    def __init__(self, parent):
        self.parent = parent
        self.count = 0
    
    def inc(self):
        Leaf.count += 1
        self.count = Leaf.count
        
    def __repr__(self):
        return 'L'
    
    def get_text(self):
        return f'{repr(self)}{self.count}'

class Frac:
    count = 0
    
    def __init__(self, parent):
        self.parent = parent
        Frac.count += 1
        self.count = Frac.count
        
    def __repr__(self):
        return 'F'
    
    def get_text(self):
        return f'{repr(self)}{self.count}'

class Zero:
    
    count = 0
    
    def __init__(self, parent):
        self.parent = parent
        Zero.count += 1
        self.count = Zero.count
        
    def __repr__(self):
        return 'Z'
    
    def get_text(self):
        return f'{repr(self)}{self.count}'

class Exists:
    count = 0
    def __init__(self, parent):
        self.parent = parent
        Exists.count += 1
        self.count = Exists.count
        
    def __repr__(self):
        return 'E'
    
    def get_text(self):
        return f'{repr(self)}{self.count}'
    
ASCII_BLOCK =  "#"
ASCII_ZERO = "0"

def is_node_left_most(node):

    if node.is_left == True and node.has_parent:
        return is_node_left_most(node.parent)
    elif node.is_left == False and node.has_parent:
        return False
    else:
        return True

class NodeMgr:
    
    def __init__(self):
        self._cache = {}
    
    def exists(self, n):
        return n in self._cache    
    
    def add(self, n):
        self._cache[n] = True
    
    def get_numbers(self):
        numbers = list(self._cache.keys())
        numbers.sort()
        return numbers

mgr = NodeMgr()

def is_node(node):
    return isinstance(node, Node)

def is_frac(node):
    return isinstance(node, Frac)

def is_zero(node):
    return isinstance(node, Zero)

def is_exists(node):
    return isinstance(node, Exists)

def is_leaf(node):
    return isinstance(node, Leaf)

class Node:
    def __init__(self, n, parent = None, is_left = None, indent = 0, depth = 0):
        self.is_left = is_left
        self.n = n
        self.parent = parent
        self.indent = indent
        self.left = Leaf(parent)
        self.right = Leaf(parent)
        env_show_info = os.getenv('SHOW_INFO')
        if env_show_info is None:
            self._show_info = False
        else:
            self._show_info = True if env_show_info.upper() == 'TRUE' else False
        self.depth = depth
        
    def add_child(self, is_left, n):
        new_node = Node(n, parent=self, is_left=is_left, depth = self.depth + 1)
        if is_left:
            self.left = new_node
        else:
            self.right = new_node
        return new_node
    
    @property
    def has_child(self):
        return isinstance(self.left, Node) or isinstance(self.right, Node)
    
    @property
    def has_parent(self):
        return self.parent is not None
    
    def __repr__(self):
        if self._show_info:
            return self.info
        else:
            return str(self.n)
    
    @property
    def children(self):
        if self.left is not None and self.right is not None:
            return f'({repr(self.left)}, {repr(self.right)})'
        elif self.right is None:
            return f'({repr(self.left)}, X)'
        
    @property
    def info(self):
        c = self.n
        p = self.parent.n if self.has_parent else 'T'
        l = self.left.n if is_node(self.left) else repr(self.left)
        r = self.right.n if is_node(self.right)  else repr(self.right)
        return f'({c}, {l}, {r}, {p})'
    
    def add_zero(self):
        self.right = Zero(self)
        return self.right
        
    def add_frac(self):
        self.right = Frac(self)
        return self.right
    
    def add_exists(self, is_left):
        if is_left:
            self.left = Exists(self)
        else:
            self.right = Exists(self)
            
def generate_tree(depth = 5):
    
    current_depth = 0
    root_node = Node(1)
    mgr.add(root_node.n)
    
    nodes = [root_node]
    
    while current_depth < depth:
        
        child_nodes = []
        
        for node in nodes:
            
            if isinstance(node, Zero) or isinstance(node, Frac) or isinstance(node, Exists):
                continue
            
            n = node.n
            
            l = n * 2
            r = (n - 1)/3
            
            if mgr.exists(l) == False:        
                mgr.add(l)
                child_nodes.append(node.add_child(True, l))
            else:
                node.add_exists(True)
            
            if r != 0 and r.is_integer():
                ir = int(r)
                if mgr.exists(ir) == False:
                    mgr.add(ir)
                    child_nodes.append(node.add_child(False, ir))
                else:
                    node.add_exists(False)
            elif r == 0:
                node.add_zero()
            elif not r.is_integer():
                node.add_frac()
        
        nodes = child_nodes
        current_depth += 1
        
    return root_node

def get_max_depth(node):
    
    if node.has_child:
        return get_max_depth(node.left)
    
    return node.depth

def get_nodes_at(node, depth):
    
    #! get the left most node and check w/ depth
    def _traverse(node):
        
        current_depth = node.depth
        
        if current_depth == depth:
            nodes.append(node)
            return
        
        if current_depth < depth and node.has_child and node.left:
            _traverse(node.left)
        
        if current_depth < depth and node.has_child and is_node(node.right):
            _traverse(node.right)
        
    nodes = []
    
    _traverse(node)
    return nodes

def get_max_value(node):
    
    def _walk_left(node):
        if node.has_child:
            return _walk_left(node.left)
        
        return node.n

    
    return _walk_left(node)
       
class CollatzPrinter:
    
    def __init__(self, root_node):
        self.root = root_node
        
        
    def render(self):
        
        max_val = get_max_value(self.root)
        node_text = str(max_val)
        strlen = len(node_text)
        
        if strlen % 2 == 0:
            max_strlen = strlen + 1
        else:
            max_strlen = strlen
                
        options = LayoutOptions(node_spacing=2,layer_spacing=3, use_ascii=True)

        def _textify(node):
            s = str(node.n)
            return s.rjust(max_strlen, ASCII_ZERO)
        
        def _walk(node):
            if is_node(node) and is_node(node.left):
                frm = _textify(node)
                to = _textify(node.left)
                G.add_edge(frm, to, side='left')
                _walk(node.left)
            
            if is_node(node) and is_node(node.right):
                frm = _textify(node)
                to = _textify(node.right)
                G.add_edge(frm, to, side='right')
                _walk(node.right)
                
            if is_node(node) and is_leaf(node.left):
                frm = _textify(node)
                child = node.left
                child.inc()
                to = child.get_text().rjust(max_strlen, ASCII_BLOCK)
                G.add_edge(frm, to, side='left')
            
            if is_node(node) and is_leaf(node.right):
                frm = _textify(node)
                child = node.right
                child.inc()
                to = child.get_text().rjust(max_strlen, ASCII_BLOCK)
                G.add_edge(frm, to, side='right')
            
            if is_node(node) and is_zero(node.right):
                frm = _textify(node)
                child = node.right
                to = child.get_text().rjust(max_strlen, ASCII_BLOCK)
                G.add_edge(frm, to, side='right')
                
            if is_node(node) and is_exists(node.right):
                frm = _textify(node)
                child = node.right
                to = child.get_text().rjust(max_strlen, ASCII_BLOCK)
                G.add_edge(frm, to, side='right')
            
            if is_node(node) and is_frac(node.right):
                frm = _textify(node)
                child = node.right
                to = child.get_text().rjust(max_strlen, ASCII_BLOCK)
                G.add_edge(frm, to, side='right')
                
        G = nx.DiGraph()
        _walk(self.root)
        
        renderer = ASCIIRenderer(G, options=options)
        
        return renderer.render()
        
try:    
    depth = int(sys.argv[1])
except:
    depth = 5

print('depth:', depth)
node = generate_tree(depth)

# test_node = node.left.left.left.left.left
# print(test_node)
# print(is_node_left_most(test_node))
print('max_depth:', get_max_depth(node))
print('max_val', get_max_value(node))

printer = CollatzPrinter(node)
print(printer.render())
