===============
senaite.jsonapi
===============

This add-on is a RESTful JSON API for `SENAITE LIMS`_, that allows to Create,
Read and Update (CRU operations) through http GET/POST requests. It uses JSON as
the format for data representation.

The development of SENAITE JSONAPI was strongly driven by the experience gained
while developing `plone.jsonapi.routes`_, with which SENAITE JSONAPI shares most
of the underlying software design solutions. The main difference between them is
that `plone.jsonapi.routes`_ is a Plone-specific RESTful JSON API, while
`senaite.jsonapi` is SENAITE-specific. For these very same reasons, this
documentation is an adapted version of `plone.jsonapi.routes's documentation`_,
with the consent of it's author.

This documentation is divided in different parts. We recommend that you get
started with :doc:`installation` and then head over to the :doc:`quickstart`.
Please check out the :doc:`api` documentation for internals about
`senaite.jsonapi`.


Table of Contents:

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   auth
   api
   crud
   extend
   doctests
   changelog


.. Links

.. _SENAITE LIMS: https://www.senaite.com
.. _plone.jsonapi.routes: https://pypi.python.org/pypi/plone.jsonapi.routes
.. _senaite.jsonapi: https://pypi.org/project/senaite.jsonapi
.. _plone.jsonapi.routes's documentation: https://plonejsonapiroutes.readthedocs.io/
