=====
fdadb
=====
|travis|_ |pypi|_ |coveralls|_ |requiresio|_

A Django wrapper for `fda.gov <https://www.fda.gov>`_ National Drug Code (NDC) database.
**fdadb** stores each row under one name **MedicationName** object instead of having multiple drugs with the same name
next to each other, for example: In the NDC database there are around 21 Viagras (with different strengths)
so in such case we save the **MedicationName: Viagra** and under this name we store all the 21 instances.
This allows for better user experience when searching through the list of drugs.

Setting Up
==========
* ``pip install fdadb``
* Add ``fdadb`` to your ``INSTALLED_APPS``
* ``./manage.py migrate fdadb``
* ``./manage.py fetch_ndc_database`` - might take 15-30 minutes (the command will fetch all items from FDA database and save it in your project)

API:
====
**All APIs are searchable with ?q=term query param.**

medications/
------------
Returns list of **MedicationName** objects (pass ``?q=termtosearch`` to filter the results),
this API supports ElasticSearch for fast querying. Pagination does not work yet when ElasticSearch is enabled
(in most cases this does not cause any issues, as this API is generally used for drug autocomplete). You can change the
autocomplete limit by setting ``FDADB_AUTOCOMPLETE_LIMIT`` in your Django configuration (default: ``10``).

The ElasticSearch uses ngram for the query parameter.

medications/(?P<medication_name>[\w-]+)/strengths
-------------------------------------------------
Returns list of medication strengths

medications/(?P<medication_name>[\w-]+)/strengths/(?P<strength_id>[\d-]+)/ndcs
------------------------------------------------------------------------------
Returns list of Medication NDCs

ElasticSearch
=============
To enable support of ElasticSearch in autocomplete, set:

* ``ELASTICSEARCH_URL`` in project configuration
* Run ``./manage.py fdadb_es_index` after fetching the NDC database (use ``--drop_indexes`` in case you want to cleanup the medications index)

Manage.py commands
==================
* ./manage.py fdadb_es_index - indexes the products into ElasticSearch
* ./manage.py fetch_ndc_database - fetches products data from NDS DB and saves in the database

Support
=======
* Django 1.11, 2.1, 2.2
* Python 3.4-3.6

.. |travis| image:: https://secure.travis-ci.org/HealthByRo/fdadb.svg?branch=master
.. _travis: http://travis-ci.org/HealthByRo/fdadb

.. |pypi| image:: https://img.shields.io/pypi/v/fdadb.svg
.. _pypi: https://pypi.python.org/pypi/fdadb

.. |coveralls| image:: https://coveralls.io/repos/github/HealthByRo/fdadb/badge.svg?branch=master
.. _coveralls: https://coveralls.io/github/HealthByRo/fdadb

.. |requiresio| image:: https://requires.io/github/HealthByRo/fdadb/requirements.svg?branch=master
.. _requiresio: https://requires.io/github/HealthByRo/fdadb/requirements/
