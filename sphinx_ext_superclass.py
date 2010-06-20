#	
#	sphinx_ext_superclass ... Sphinx extension to fix superclass and monkey-patching signatures.
#	Copyright (C) 2010  KennyTM~ <kennytm@gmail.com>
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#	

from docutils import nodes
from docutils.parsers.rst import Directive, directives

class flushRightNode(nodes.TextElement, nodes.Element):
	pass

def visit_flushRightNode(self, node):
	self.body.append(self.starttag(node, 'p', CLASS="flushRight"))
	
def depart_flushRightNode(self, node):
	self.body.append('</p>')


class FlushRightDirective(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        if not self.arguments:
            return []
        (inodes, messages) = self.state.inline_text(self.arguments[0], self.lineno)
        subnode = flushRightNode()
        subnode.extend(inodes)
        return [subnode] + messages



def process_sig_for_monkey_patches(app, what, name, obj, options, signature, return_annotation):
	if hasattr(obj, 'sphinx_monkeyPatched'):
		return (None, None)

def process_base_for_classes(app, what, name, obj, options, docstring):
	if what == 'class':
		bases = [(u':class:`%s.%s`' % (x.__module__, x.__name__) if x.__module__ != '__builtin__' else x.__name__)
				 for x in obj.__bases__ if x is not object]
		if bases:
			prefix = 'Patching: ' if hasattr(obj, 'sphinx_monkeyPatched') else ('Superclasses: ' if len(bases) > 1 else 'Superclass: ')
			docstring.insert(0, '')
			docstring.insert(0, u'.. efflushright:: ' + prefix + u', '.join(bases))
			

def setup(app):
	app.add_node(flushRightNode, html=(visit_flushRightNode, depart_flushRightNode))
	app.add_directive('efflushright', FlushRightDirective)
	app.connect('autodoc-process-signature', process_sig_for_monkey_patches)
	app.connect('autodoc-process-docstring', process_base_for_classes)
