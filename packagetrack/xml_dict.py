"""
Helpers functions to convert nested dicts/lists to and from XML.

For example, this XML:

    <foo>
      <bar>
        <baz>what</baz>
        <quux>hello</quux>
      </bar>
      <sup>yeah</sup>
      <goodbye>no</goodbye>
    </foo>

Will be transformed to and from this dict:

    {'foo': {'bar': {'baz': 'what',
                     'quux': 'hello'},
             'sup': 'yeah',
             'goodbye': 'no'}}
"""

from xml.dom.minidom import getDOMImplementation, parseString


def dict_to_doc(d, attrs=None):
    assert len(d) == 1
    impl = getDOMImplementation()
    doc = impl.createDocument(None, d.keys()[0], None)

    def dict_to_nodelist(d, parent):
        for key, child in d.iteritems():
            new = doc.createElement(key)
            parent.appendChild(new)
            if type(child) == dict:
                dict_to_nodelist(child, new)
            else:
                new.appendChild(doc.createTextNode(child))

    if attrs:
        for key, val in attrs.iteritems():
            doc.documentElement.setAttribute(key, val)

    dict_to_nodelist(d.values()[0], doc.documentElement)
    return doc


def dict_to_xml(d, attrs=None):
    return dict_to_doc(d, attrs).toxml()

def xml_to_dict(s):
    """Convert XML data to a Python dict"""
    return nodeToDict(parseString(s))

class NotTextNodeError: pass

def getTextFromNode(node):
    """
    scans through all children of node and gathers the
    text. if node has non-text child-nodes, then
    NotTextNodeError is raised.
    """
    t = ""
    for n in node.childNodes:
        if n.nodeType == n.TEXT_NODE:
            t += n.nodeValue
        else:
            raise NotTextNodeError
    return t

def nodeToDict(node):
    """Convert a minidom node to dict"""
    dic = {}
    for n in node.childNodes:
        if n.nodeType != n.ELEMENT_NODE:
            continue

        # we've seen this element before, so we make it a list
        if n.nodeName in dic and type(dic[n.nodeName]) != list:
            dic[n.nodeName] = [dic[n.nodeName]]

        try:
            text = getTextFromNode(n)
        except NotTextNodeError:
            if n.nodeName in dic and type(dic[n.nodeName]) == list:
                dic[n.nodeName].append(nodeToDict(n))
            else:
                dic.update({n.nodeName:nodeToDict(n)})
            continue

        # text node
        if n.nodeName in dic and type(dic[n.nodeName]) == list:
            dic[n.nodeName].append(text)
        else:
            dic.update({n.nodeName:text})

    return dic

