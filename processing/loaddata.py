# coding: utf-8
import logging
from datetime import datetime, timedelta
import argparse
import os
import sys

import requests
from elasticsearch_dsl import connections
from xylose.scielodocument import Article, Journal

from publication import utils, es_persistence
import choices

logger = logging.getLogger(__name__)

config = utils.Configuration.from_env()
settings = dict(config.items())

ARTICLEMETA = "http://localhost:7000/api/v1"
ISO_3166_COUNTRY_AS_KEY = {value: key for key, value in choices.ISO_3166.items()}

FROM = datetime.now() - timedelta(days=30)
FROM.isoformat()[:10]

connections.connections.create_connection(hosts=[settings['app:main']['elasticsearch']], timeout=360)

publication = {}


def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)

    return logger


def do_request(url, params):

    try:
        response = requests.get(url, params=params).json()
    except:
        logger.error('Fail to load url: %s, %s' % (url, str(params)))
        return None

    return response


def fmt_document(document):
    return document


def fmt_journal(document):
    ESjournal = es_persistence.Journal()

    ESjournal.id = '_'.join([document.collection_acronym, document.scielo_issn])
    ESjournal._id = ESjournal.id
    ESjournal.issn = document.scielo_issn
    ESjournal.collection = document.collection_acronym
    ESjournal.subject_areas = document.subject_areas
    ESjournal.included_at_year = document.creation_date[0:4]
    ESjournal.status = document.current_status
    ESjournal.title = document.title
    permission = document.permissions or {'id': 'undefined'}
    ESjournal.license = permission.get('id' or 'undefined')

    yield ESjournal


def country(country):
    if country in choices.ISO_3166:
        return country
    if country in ISO_3166_COUNTRY_AS_KEY:
        return ISO_3166_COUNTRY_AS_KEY[country]
    return 'undefined'


def pages(first, last):

    try:
        pages = int(last)-int(first)
    except:
        pages = 0

    if pages >= 0:
        return pages
    else:
        return 0

def acceptancedelta(received, accepted):

    try:
        rec = datetime.strptime(received,'%Y-%m-%d')
    except:
        return None

    try:
        acc = datetime.strptime(accepted,'%Y-%m-%d')
    except:
        return None

    delta = acc-rec

    days = delta.days

    if days >= 0:
        return days

def fmt_article(document, collection='BR'):
    ESarticle = es_persistence.Article()

    ESarticle.id = '_'.join([document.collection_acronym, document.publisher_id])
    ESarticle._id = ESarticle.id
    ESarticle.pid = document.publisher_id
    ESarticle.issn = document.journal.scielo_issn
    ESarticle.journal_title = document.journal.title
    ESarticle.issue = '_'.join([document.collection_acronym, document.publisher_id[0:18]])
    ESarticle.processing_year = document.processing_date[0:4]
    ESarticle.processing_date = document.processing_date
    ESarticle.publication_date = document.publication_date
    ESarticle.publication_year = document.publication_date[0:4]
    subject_areas = document.journal.subject_areas or ['undefined']
    ESarticle.subject_areas = [i for i in subject_areas]
    ESarticle.collection = document.collection_acronym
    ESarticle.document_type = document.document_type
    pgs = pages(document.start_page, document.end_page)
    ESarticle.pages = pgs
    ESarticle.languages = list(set(document.languages()+[document.original_language() or 'undefined']))
    ESarticle.aff_countries = ['undefined']
    if document.mixed_affiliations:
        ESarticle.aff_countries = list(set([country(aff.get('country', 'undefined')) for aff in document.mixed_affiliations]))
    ESarticle.citations = len(document.citations or [])
    ESarticle.authors = len(document.authors or [])
    permission = document.permissions or {'id': 'undefined'}
    ESarticle.license = permission.get('id' or 'undefined')
    if document.doi:
        ESarticle.doi = document.doi
        ESarticle.doi_prefix = document.doi.split('/')[0]

    delta = acceptancedelta(document.receive_date, document.acceptance_date)
    if delta:
        ESarticle.acceptance_delta = delta

    yield ESarticle

def fmt_citation(document, collection='BR'):

    for citation in document.citations or []:
        EScitation = es_persistence.Citation()
        EScitation.id = '_'.join([document.collection_acronym, document.publisher_id, str(citation.index_number)])
        EScitation._id = EScitation.id
        EScitation.pid = document.publisher_id
        EScitation.citation_type = citation.publication_type
        if citation.date:
            EScitation.publication_year = citation.date[0:4]
        EScitation.collection = document.collection_acronym

        yield EScitation


def documents(endpoint, fmt=None, from_date=FROM, identifiers=False):

    allowed_endpoints = ['journal', 'article', 'citation']

    mode = 'history'

    if identifiers:
        mode = 'identifiers'

    if not endpoint in allowed_endpoints:
        raise TypeError('Invalid endpoint, expected one of: %s' % str(allowed_endpoints))

    params = {'offset': 0, 'from': from_date}

    if endpoint == 'article':
        xylose_model = Article
    elif endpoint == 'journal':
        xylose_model = Journal

    while True:
        identifiers = do_request(
            '{0}/{1}/{2}'.format(ARTICLEMETA, endpoint, mode),
            params
        )

        logger.debug('offset %s' % str(params['offset']))

        logger.debug('len identifiers %s' % str(len(identifiers['objects'])))

        if len(identifiers['objects']) == 0:
            raise StopIteration

        for identifier in identifiers['objects']:
            dparams = {
                'collection': identifier['collection']
            }

            if endpoint == 'article':
                dparams['code'] = identifier['code']
                if dparams['code'] == None:
                    continue

            elif endpoint == 'journal':
                dparams['issn'] = identifier['code'][0]
                if dparams['issn'] == None:
                    continue

            document = do_request('{0}/{1}'.format(ARTICLEMETA, endpoint), dparams)

            if not document:
                continue

            if 'event' in identifier and identifier['event'] == 'delete':
                dparams['id'] = '_'.join([dparams['collection'], dparams['code']])
                yield (identifier['event'], dparams)
                continue

            if isinstance(document, dict):
                doc_ret = document
            elif isinstance(document, list):
                doc_ret = document[0]

            for item in fmt(xylose_model(doc_ret)):
                yield ('add', item)

        params['offset'] += 1000


def run(doc_type, from_date=FROM, identifiers=False):

    try:
        es_persistence.publication.create()
    except:
        logger.debug('Index already available')

    if doc_type == 'journal':
        endpoint = 'journal'
        fmt = fmt_journal
    elif doc_type == 'article':
        endpoint = 'article'
        fmt = fmt_article
    elif doc_type == 'citation':
        endpoint = 'article'
        fmt = fmt_citation
    else:
        logger.error('Invalid doc_type: %s'%doc_type)
        exit()

    for event, document in documents(endpoint, fmt, from_date=from_date, identifiers=identifiers):
        if event == 'delete':
            logger.debug('removing document %s from index %s' % (document['id'], doc_type))
            try:
                document.delete()
            except NotFoundError:
                logger.debug('Record already removed: %s' % document['id'])
            except:
                logger.error('Unexpected error: %s' % sys.exc_info()[0])

        else: # event would be ['add', 'update']
            logger.debug('loading document %s into index %s' % (document['id'], doc_type))
            document.save()


        
def main():

    parser = argparse.ArgumentParser(
        description="Load SciELO Network data no analytics production"
    )

    parser.add_argument(
        '--from_date',
        '-f',
        default=FROM,
        help='ISO date like 2013-12-31'
    )

    parser.add_argument(
        '--identifiers',
        '-i',
        action='store_true',
        help='Define the identifiers endpoint to retrieve the document and journal codes. If not given the enpoint used will be the history. When using history the processing will also remove records from the index.'
    )

    parser.add_argument(
        '--logging_file',
        '-o',
        help='Full path to the log file'
    )

    parser.add_argument(
        '--doc_type',
        '-d',
        choices=['article', 'journal', 'citation'],
        help='Document type that will be updated'
    )

    parser.add_argument(
        '--logging_level',
        '-l',
        default='DEBUG',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logggin level'
    )

    args = parser.parse_args()

    _config_logging(args.logging_level, args.logging_file)

    run(doc_type=args.doc_type, from_date=args.from_date, identifiers=args.identifiers)
