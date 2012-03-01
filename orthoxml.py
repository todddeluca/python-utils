'''

From http://orthoxml.org/0.3/orthoxml_doc_v0.3.html:
OrthoXML is an XML schema designed to describe orthology relations. Orthologs
are defined as genes in different species deriving from a single gene in the
last common ancestor. This relationship makes them interesting, as they are
likely to have the same function.

OrthoXML is designed to be a versatile format to store orthology data from
different sources in a uniform manner. It can store assignment from both
pairwise approaches and tree based approaches with a variable level of detail.
OrthoXML allows direct comparison and integration of orthology data from
different resources. Additional, resource-specific information can also be
included.

OrthoXML is a XML format. XML is a markup language which embeds the content in
a structured way so that it easy to process and validate. Orthology data can be
structured using XML as a container, where the relationships of genes and their
orthology groups can be described as data objects. Since OrthoXML is defined as
an XML schema, all XML files can be validated and checked to see if they are
well-formed documents.

http://www.orthoxml.org/xml/Main.html
http://www.orthoxml.org/0.3/examples/orthoxml_example_v0.3.xml
http://www.orthoxml.org/0.3/orthoxml.xsd
http://orthoxml.org/0.3/orthoxml_doc_v0.3.html

'''

def test():
    import sys
    gene = Gene("3", "P1234", protId="Q1341", transcriptId="P1234t")
    database = Database("Uniprot", "2011_06", genes=[gene], protLink="http://www.uniprot.org/uniprot/")
    species = Species("Mus musculus", "10090", [database], notes=Notes("uniprot mouse rocks!"))
    gene2 = Gene("4", "Q1234", protId="R9999")
    gene3 = Gene("5", "Q1235", protId="R6678")
    database2 = Database("Uniprot", "2011_06", genes=[gene2, gene3], geneLink="http://www.uniprot.org/uniprot/",
                                  protLink="http://www.uniprot.org/uniprot/", transcriptLink="http://www.uniprot.org/uniprot/")
    species2 = Species("Homo sapiens", "9606", [database2], notes=Notes("uniprot human rocks!"))
    notes2 = Notes("ortho notes")
    notes3 = Notes("group notes")
    scoredef = ScoreDef("dist", "maximum-likelihood evolutionary distance, from 0.0 to 19.0")
    score =Score("dist", "1.039")
    geneRef1 = GeneRef("3", notes=Notes("generef 3 is cool"))
    geneRef2 = GeneRef("4", scores=[Score("dist", "1.1"), Score("dist", "1.2")])
    geneRef3 = GeneRef("5", notes=Notes("generef 3 is cool"))
    prop1 = Property("speed", "fast")
    prop2 = Property("valuable")
    pgroup = ParalogGroup([geneRef2, geneRef3], properties=[prop1, prop2], iden="p1", scores=[score], notes=Notes("good job"))
    ogroup = OrthologGroup([pgroup, geneRef1], scores=[score], notes=Notes("good job"))
    for x in toOrthoXML("roundup", "2", [species, species2], [ogroup], scoreDefs=[scoredef], notes=Notes("params look ok"), indent=' ', newl='\n'):
        sys.stdout.write(x)
      

class Notes(object):
    def __init__(self, notes):
        '''
        notes: a string describing something
        '''
        self.notes = notes

    def toXml(self, indent, newl, level):
        if self.notes:
            yield indent*level + '<notes>' + newl
            yield indent*(level+1) + self.notes.strip() + newl
            yield indent*level + '</notes>' + newl
        else:
            yield indent*level + '<notes/>' + newl


class Gene(object):
    def __init__(self, iden, geneId=None, protId=None, transcriptId=None):
        '''
        iden: required.  the integer (or string of an integer) id used to identify the gene in the orthoxml document.
          Unique among other gene ids in the document.
        geneId: an external gene identifier, presumably from the database associated with this Gene.
        protId: an external protein identifier, presumably from the database associated with this Gene.
        transcriptId: an external transcript identifier, presumably from the database associated with this Gene.
        At least one of geneId, protId, and transcriptId is required.
        '''
        self.id = int(iden)
        self.geneId = geneId
        self.protId = protId
        self.transcriptId = transcriptId

    def toXml(self, indent, newl, level):
        tag = '<gene id="{}"'.format(self.id)
        tag += ''.join(' {}="{}"'.format(k, getattr(self, k)) for k in ('geneId', 'protId', 'transcriptId') if getattr(self, k) is not None) + '/>' + newl
        yield indent*level + tag


class ScoreDef(object):
    def __init__(self, iden, desc):
        '''
        iden: required.  used to identify this score definition in the document.
        desc: a description of what type of score this is, e.g. BLAST E-value.
        '''
        self.id = iden
        self.desc = desc

    def toXml(self, indent, newl, level):
        yield indent*level + '<scoreDef id="{}" desc="{}"/>{}'.format(self.id, self.desc, newl)



class Score(object):
    def __init__(self, iden, value):
        '''
        iden: required.  refers to a ScoreDef id, which defines the type of this score.
        value: the actual score itself.
        '''
        self.id = iden
        self.value = value

    def toXml(self, indent, newl, level):
        yield indent*level + '<score id="{}" value="{}"/>{}'.format(self.id, self.value, newl)


class Property(object):
    def __init__(self, name, value=None):
        '''
        key: required.
        value: optional, in case the property key is a flag.
        From the orthoxml docs: Key-value pair for group annotations, for instance statistics about the group members.
        '''
        self.name = name
        self.value = value
        
    def toXml(self, indent, newl, level):
        tag = '<property name="{}"'.format(self.name)
        tag += ' value="{}"/>{}'.format(self.value, newl) if self.value is not None else '/>{}'.format(newl)
        yield indent*level + tag


class Database(object):
    def __init__(self, name, version, genes, geneLink=None, protLink=None, transcriptLink=None):
        '''
        name: e.g. Ensembl or Uniprot.  The name of the database where the genes come from.
        version: The version or release these genes are from.  e.g. Homo_sapiens.NCBI36.52.pep.all.fa or 2011_06
        genes: a seq of at least 1 Gene object.  these genes belong to this database in this species.
        geneLink: optional url 
        protLink: optional url
        transcriptLink: optioal url
        see the orthoxml docs for more about the links.
        '''
        self.name = name
        self.version = version
        self.genes = genes
        self.geneLink = geneLink
        self.protLink = protLink
        self.transcriptLink = transcriptLink
        
    def toXml(self, indent, newl, level):
        tag = '<database name="{}" version="{}"'.format(self.name, self.version)
        tag += ''.join(' {}="{}"'.format(k, getattr(self, k)) for k in ('geneLink', 'protLink', 'transcriptLink') if getattr(self, k) is not None) + '>{}'.format(newl)
        yield indent*level + tag
        yield indent*(level+1) + '<genes>{}'.format(newl)
        for gene in self.genes:
            for xml in gene.toXml(indent, newl, level+2):
                yield xml
        yield indent*(level+1) + '</genes>{}'.format(newl)
        yield indent*level + '</database>{}'.format(newl)


class Species(object):
    def __init__(self, name, ncbiTaxId, databases, notes=None):
        '''
        name: e.g. Homo sapiens.  An organism name.
        ncbiTaxId: an integer, e.g. 9606.  The NCBI Taxonomy database id corresponding to this species.
        databases: a seq of at least one Database obj.
        notes: optional Notes object annotating this species.
        '''
        self.name = name
        self.ncbiTaxId = int(ncbiTaxId)
        self.databases = databases
        self.notes = notes

    def toXml(self, indent, newl, level):
        yield indent*level + '<species name="{}" NCBITaxId="{}">{}'.format(self.name, self.ncbiTaxId, newl)
        for database in self.databases:
            for xml in database.toXml(indent, newl, level+1):
                yield xml
        if self.notes:
            for xml in self.notes.toXml(indent, newl, level+1):
                yield xml
        yield indent*level + '</species>{}'.format(newl)

    
class OrthologGroup(object):
    def __init__(self, members, iden=None, scores=None, properties=None, notes=None):
        '''
        iden: identifier for the group of orthologs in the origin of this orthoxml document.  optional, but recommened if it is available.
        members: a list of 2 or more elements, where each element can be a GeneRef, OrthologGroup, or ParalogGroup
        scores: optional.  a seq of zero or more Score objs describing this group.
        properties: optional.  a seq of of 0 or more Property objs describing this group.
        notes: an optional Notes object about this group.
        Members of an OrthologGroup are related by a speciation event at their most recent point of origin.
        '''
        self.id = iden
        self.scores = scores if scores is not None else []
        self.properties = properties if properties is not None else []
        self.members = members
        self.notes = notes

    def toXml(self, indent, newl, level):
        tag = '<orthologGroup id="{}"/>{}'.format(self.id, newl) if self.id else '<orthologGroup>{}'.format(newl)
        yield indent*level + tag
        for score in self.scores:
            for xml in score.toXml(indent, newl, level+1):
                yield xml
        for prop in self.properties:
            for xml in prop.toXml(indent, newl, level+1):
                yield xml
        for member in self.members:
            for xml in member.toXml(indent, newl, level+1):
                yield xml
        if self.notes:
            for xml in self.notes.toXml(indent, newl, level+1):
                yield xml
        yield indent*level + '</orthologGroup>{}'.format(newl)

        
class ParalogGroup(object):
    def __init__(self, members, iden=None, scores=None, properties=None, notes=None):
        '''
        iden: identifier for the group of orthologs in the origin of this orthoxml document.  optional, but recommened if it is available.
        members: a list of 2 or more elements, where each element can be a GeneRef, OrthologGroup, or ParalogGroup
        scores: optional.  a seq of zero or more Score objs describing this group.
        properties: optional.  a seq of of 0 or more Property objs describing this group.
        notes: an optional Notes object about this group.
        Members of a ParalogGroup are related by a duplication event at their most recent point of origin.
        '''
        self.id = iden
        self.scores = scores if scores is not None else []
        self.properties = properties if properties is not None else []
        self.members = members
        self.notes = notes

    def toXml(self, indent, newl, level):
        tag = '<paralogGroup id="{}"/>{}'.format(self.id, newl) if self.id else '<paralogGroup>{}'.format(newl)
        yield indent*level + tag
        for score in self.scores:
            for xml in score.toXml(indent, newl, level+1):
                yield xml
        for prop in self.properties:
            for xml in prop.toXml(indent, newl, level+1):
                yield xml
        for member in self.members:
            for xml in member.toXml(indent, newl, level+1):
                yield xml
        if self.notes:
            for xml in self.notes.toXml(indent, newl, level+1):
                yield xml
        yield indent*level + '</paralogGroup>{}'.format(newl)

        
class GeneRef(object):
    def __init__(self, iden, scores=None, notes=None):
        '''
        iden: a Gene id
        scores: optional.  a seq of zero or more Score objs describing this GeneRef.
        notes: optional.  Notes object describing this GeneRef.
        '''
        self.id = int(iden)
        self.scores = scores if scores is not None else []
        self.notes = notes

    def toXml(self, indent, newl, level):
        if self.notes or self.scores:
            yield indent*level + '<geneRef id="{}">{}'.format(self.id, newl)
            for score in self.scores:
                for xml in score.toXml(indent, newl, level+1):
                    yield xml
            if self.notes:
                for xml in self.notes.toXml(indent, newl, level+1):
                    yield xml
            yield indent*level + '</geneRef>{}'.format(newl)
        else:
            yield indent*level + '<geneRef id="{}"/>{}'.format(self.id, newl)

    
def toOrthoXML(origin, originVersion, species, groups, scoreDefs=None, notes=None, version='0.3', indent=' ', newl='\n'):
    '''
    origin: the source of these ortholog groups.  e.g. inparanoid, roundup, omabrowser.
    originVersion: the version or release of the source database.  e.g 2, 7.0, GRCh37.p5, 2011_06.
    species: a iterable of Species objects.  These species contain the databases which contain the genes that are referred to within the groups.
    Iterable so items can be generated on the fly to avoid memory issues.
    groups: an iterable of one or more OrthologGroup objects.  Iterable so items can be generated on the fly to avoid memory issues.
    scoreDefs: optional. a seq of zero or more ScoreDef objects.  These are referred to by the Score elements of groups and gene refs.
    notes: an optional notes object describing the origin and other details about these orthologs.
    To avoid constructing the entire document in memory or holding all groups in memory, this function takes an iterable groups and yields string pieces of the xml
    document.  Useful for writing to a file, a network socket, etc.
    returns: a generator that yields strings which can be concatenated to form an xml document.  
    '''
    level = 0
    yield '<?xml version="1.0" encoding="utf-8"?>' + newl
    rootStart = '<orthoXML xmlns="http://orthoXML.org/2011/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="{}" '.format(version)
    rootStart += 'origin="{}" originVersion="{}" xsi:schemaLocation="http://orthoXML.org/2011/ http://www.orthoxml.org/0.3/orthoxml.xsd">{}'.format(origin, originVersion, newl)
    yield rootStart
    
    if notes:
        for xml in notes.toXml(indent, newl, level+1):
            yield xml

    # yield species one at a time b/c they can be big, containing tens of thousands of genes.
    for spec in species:
        for xml in spec.toXml(indent, newl, level+1):
            yield xml

    if scoreDefs:
        yield indent*(level+1) + '<scores>{}'.format(newl)
        for scoreDef in scoreDefs:
            for xml in scoreDef.toXml(indent, newl, level+2):
                yield xml            
        yield indent*(level+1) + '</scores>{}'.format(newl)

    # yield groups one at a time, b/c there could be very many of them, too many to hold in memory
    yield indent*(level+1) + '<groups>{}'.format(newl)
    for group in groups:
        for xml in group.toXml(indent, newl, level+2):
            yield xml
    yield indent*(level+1) + '</groups>{}'.format(newl)

    rootEnd = '</orthoXML>{}'.format(newl)
    yield rootEnd


if __name__ == '__main__':
    pass
