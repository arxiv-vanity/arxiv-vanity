from django import template
import randomcolor

register = template.Library()

CATEGORY_NAMES = {
    'cs.AI': 'Artificial Intelligence',
    'cs.CL': 'Computation and Language',
    'cs.CC': 'Computational Complexity',
    'cs.CE': 'Computational Engineering',
    'cs.CG': 'Computational Geometry',
    'cs.GT': 'Game Theory',
    'cs.CV': 'Computer Vision',
    'cs.CY': 'Computers and Society',
    'cs.CR': 'Cryptography and Security',
    'cs.DS': 'Data Structures and Algorithms',
    'cs.DB': 'Databases',
    'cs.DL': 'Digital Libraries',
    'cs.DM': 'Discrete Mathematics',
    'cs.DC': 'Distributed Computing',
    'cs.ET': 'Emerging Technologies',
    'cs.FL': 'Formal Languages',
    'cs.GL': 'General Literature',
    'cs.GR': 'Graphics',
    'cs.AR': 'Hardware Architecture',
    'cs.HC': 'Human-Computer Interaction',
    'cs.IR': 'Information Retrieval',
    'cs.IT': 'Information Theory',
    'cs.LG': 'Learning',
    'cs.LO': 'Logic',
    'cs.MS': 'Mathematical Software',
    'cs.MA': 'Multiagent Systems',
    'cs.MM': 'Multimedia',
    'cs.NI': 'Networking and Internet',
    'cs.NE': 'Neural and Evolutionary Computing',
    'cs.NA': 'Numerical Analysis',
    'cs.OS': 'Operating Systems',
    'cs.PF': 'Performance',
    'cs.PL': 'Programming Languages',
    'cs.RO': 'Robotics',
    'cs.SI': 'Social and Information Networks',
    'cs.SE': 'Software Engineering',
    'cs.SD': 'Sound',
    'cs.SC': 'Symbolic Computation',
    'cs.SY': 'Systems and Control',
    'stat.ML': 'Machine Learning',
}

@register.inclusion_tag('papers/templatetags/category_badge.html')
def category_badge(category):
    if category not in CATEGORY_NAMES:
        return {}
    return {
        'category': category,
        'name': CATEGORY_NAMES[category],
        'color': randomcolor.RandomColor(category).generate(luminosity='dark')[0],
    }
