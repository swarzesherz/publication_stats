from elasticsearch_dsl import Index, DocType, String

publication = Index('publication_test')

@publication.doc_type
class Article(DocType):

    id = String(index='not_analyzed')
    pid = String(index='not_analyzed')
    issn = String(index='not_analyzed')
    issue = String(index='not_analyzed')
    subject_areas = String(index='not_analyzed')
    collection = String(index='not_analyzed')
    languages = String(index='not_analyzed')
    aff_countries = String(index='not_analyzed')
    document_type = String(index='not_analyzed')
    journal_title = String(index='not_analyzed')
    license = String(index='not_analyzed')
    processing_year = String(index='not_analyzed')
    processing_date = String(index='not_analyzed')
    publication_year = String(index='not_analyzed')
    publication_date = String(index='not_analyzed')
    doi = String(index='not_analyzed')
    doi_prefix = String(index='not_analyzed')

    class Meta:
        index = 'publication_test'

    def save(self, ** kwargs):
        return super(Article, self).save(** kwargs)

@publication.doc_type
class Journal(DocType):

    id = String(index='not_analyzed')
    collection = String(index='not_analyzed')
    issn = String(index='not_analyzed')
    subject_area = String(index='not_analyzed')
    title = String(index='not_analyzed')
    included_at_year = String(index='not_analyzed')
    status = String(index='not_analyzed')
    license = String(index='not_analyzed')

    class Meta:
        index = 'publication_test'

    def save(self, ** kwargs):
        return super(Journal, self).save(** kwargs)

@publication.doc_type
class Citation(DocType):

    id = String(index='not_analyzed')
    collection = String(index='not_analyzed')
    pid = String(index='not_analyzed')
    citation_type = String(index='not_analyzed')
    publication_year = String(index='not_analyzed')

    class Meta:
        index = 'publication_test'

    def save(self, ** kwargs):
        return super(Citation, self).save(** kwargs)
