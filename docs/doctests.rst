Doctests
========

.. include:: ../src/senaite/jsonapi/tests/doctests/version.rst
.. include:: ../src/senaite/jsonapi/tests/doctests/search.rst
.. include:: ../src/senaite/jsonapi/tests/doctests/create.rst


Restrictions
~~~~~~~~~~~~

We get a 401 error if we try to create an object inside portal root:

    >>> data = {"title": "My clients folder",
    ...         "portal_type": "ClientsFolder",
    ...         "parent_path": api.get_path(portal)}
    >>> post("create", data)
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 401: Unauthorized

We get a 401 error if we try to create an object inside setup folder:

    >>> data = {"title": "My Analysis Categories folder",
    ...         "portal_type": "AnalysisCategories",
    ...         "parent_path": api.get_path(setup)}
    >>> post("create", data)
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 401: Unauthorized

We get a 401 error when we try to create an object from a type that is not
allowed by the container:

    >>> data = {"title": "My Method",
    ...         "portal_type": "Method",
    ...         "parent_path": api.get_path(clients)}
    >>> post("create", data)
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 401: Unauthorized


    >>> data = {"portal_type": "SampleType",
    ...         "parent_path": api.get_path(setup.bika_sampletypes),
    ...         "title": "Fresh Egg",
    ...         "Prefix": "FE"}
    >>> sample_type = create(data)

    >>> data = {"portal_type": "LabContact",
    ...         "parent_path": api.get_path(setup.bika_labcontacts),
    ...         "Firstname": "Lab",
    ...         "Lastname": "Chicken"}
    >>> lab_contact = create(data)

    >>> data = {"portal_type": "Department",
    ...         "parent_path": api.get_path(setup.bika_departments),
    ...         "title": "Microbiology",
    ...         "Manager": api.get_uid(lab_contact)}
    >>> department = create(data)

    >>> data = {"portal_type": "AnalysisCategory",
    ...         "parent_path": api.get_path(setup.bika_analysiscategories),
    ...         "title": "Microbiology identification",
    ...         "Department": api.get_uid(department)}
    >>> category = create(data)

    >>> data = {"portal_type": "AnalysisService",
    ...         "parent_path": api.get_path(setup.bika_analysisservices),
    ...         "title": "Salmonella",
    ...         "Keyword": "Sal",
    ...         "ScientificName": True,
    ...         "Price": 15,
    ...         "Category": api.get_uid(category),
    ...         "Accredited": True}
    >>> sal = create(data)

    >>> data = {"portal_type": "AnalysisService",
    ...         "parent_path": api.get_path(setup.bika_analysisservices),
    ...         "title": "Escherichia coli",
    ...         "Keyword": "Ecoli",
    ...         "ScientificName": True,
    ...         "Price": 15,
    ...         "Category": api.get_uid(category)}
    >>> ecoli = create(data)

Now that we have the basic objects in place, let's create a Sample:

    >>> data = {"portal_type": "AnalysisRequest",
    ...         "Client": api.get_uid(client),
    ...         "Contact": api.get_uid(contact),
    ...         "DateSampled": DateTime().ISO8601(),
    ...         "SampleType": api.get_uid(sample_type),
    ...         "Analyses": map(api.get_uid, [sal, ecoli]) }
    >>> sample = create(data)
    >>> sample