CREATE
------

Running this test from the buildout directory:

    bin/test test_doctests -t create


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from DateTime import DateTime
    >>> from operator import itemgetter
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

    >>> from bika.lims import api

Functional Helpers:

    >>> def login(user=TEST_USER_ID, password=TEST_USER_PASSWORD):
    ...     browser.open(portal_url + "/login_form")
    ...     browser.getControl(name='__ac_name').value = user
    ...     browser.getControl(name='__ac_password').value = password
    ...     browser.getControl(name='submit').click()
    ...     assert("__ac_password" not in browser.contents)

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, urllib.urlencode(data, doseq=True))
    ...     return browser.contents

    >>> def create(data):
    ...     response = post("create", data)
    ...     assert("items" in response)
    ...     response = json.loads(response)
    ...     items = response.get("items")
    ...     assert(len(items)==1)
    ...     item = response.get("items")[0]
    ...     assert("uid" in item)
    ...     return api.get_object(item["uid"])

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setup = api.get_setup()
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


Create with resource
~~~~~~~~~~~~~~~~~~~~

Authenticate:

    >>> login()

We can create an object by providing the resource and the parent uid directly
in the request:

    >>> clients = portal.clients
    >>> clients_uid = api.get_uid(clients)
    >>> url = "client/create/{}".format(clients_uid)
    >>> data = {"title": "Test client 1",
    ...         "ClientID": "TC1"}
    >>> post(url, data)
    '...clients/client-1"...'

We can also omit the parent uid while defining the resource, but passing the
uid of the container via post:

    >>> data = {"title": "Test client 2",
    ...         "ClientID": "TC2",
    ...         "parent_uid": clients_uid}
    >>> post("client/create", data)
    '...clients/client-2"...'

We can use `parent_path` instead of `parent_uid`:

    >>> data = {"title": "Test client 3",
    ...         "ClientID": "TC3",
    ...         "parent_path": api.get_path(clients)}
    >>> post("client/create", data)
    '...clients/client-3"...'


Create without resource
~~~~~~~~~~~~~~~~~~~~~~~

Or we can create an object without the resource, but with the parent uid and
defining the portal_type via post:

    >>> url = "create/{}".format(clients_uid)
    >>> data = {"title": "Test client 4",
    ...         "ClientID": "TC4",
    ...         "portal_type": "Client"}
    >>> post(url, data)
    '...clients/client-4"...'


Create via post only
~~~~~~~~~~~~~~~~~~~~

We can omit both the resource and container uid and pass everything via post:

    >>> data = {"title": "Test client 5",
    ...         "ClientID": "TC5",
    ...         "portal_type": "Client",
    ...         "parent_path": api.get_path(clients)}
    >>> post("create", data)
    '...clients/client-5"...'

    >>> data = {"title": "Test client 6",
    ...         "ClientID": "TC6",
    ...         "portal_type": "Client",
    ...         "parent_uid": clients_uid}
    >>> post("create", data)
    '...clients/client-6"...'

If we do a search now for clients, we will get all them:

    >>> output = get("client")
    >>> output = json.loads(output)
    >>> items = output.get("items")
    >>> items = map(lambda it: it.get("getClientID"), items)
    >>> sorted(items)
    [u'TC1', u'TC2', u'TC3', u'TC4', u'TC5', u'TC6']


Required fields
~~~~~~~~~~~~~~~

System will fail with a 400 error when trying to create an object without a
required attribute:

    >>> data = {"portal_type": "SampleType",
    ...         "parent_path": api.get_path(setup.bika_sampletypes),
    ...         "title": "Fresh Egg",
    ...         "Prefix": "FE"}
    >>> post("create", data)
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 400: Bad Request


Create a Client
~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "Client",
    ...         "parent_path": api.get_path(clients),
    ...         "title": "Omelette corp",
    ...         "ClientID": "EC"}
    >>> client = create(data)
    >>> client.getClientID()
    'EC'
    >>> api.get_parent(client)
    <ClientFolder at /plone/clients>


Create a Client Contact
~~~~~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "Contact",
    ...         "parent_path": api.get_path(client),
    ...         "Firstname": "Proud",
    ...         "Surname": "Hen"}
    >>> contact = create(data)
    >>> contact.getFullname()
    'Proud Hen'
    >>> api.get_parent(contact)
    <Client at /plone/clients/client-7>


Create a Sample Type
~~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "SampleType",
    ...         "parent_path": api.get_path(setup.bika_sampletypes),
    ...         "title": "Fresh Egg",
    ...         "MinimumVolume": "10 gr",
    ...         "Prefix": "FE"}
    >>> sample_type = create(data)
    >>> sample_type.Title()
    'Fresh Egg'
    >>> sample_type.getPrefix()
    'FE'
    >>> api.get_parent(sample_type)
    <SampleTypes at /plone/bika_setup/bika_sampletypes>


Create a Laboratory Contact
~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "LabContact",
    ...         "parent_path": api.get_path(setup.bika_labcontacts),
    ...         "Firstname": "Lab",
    ...         "Surname": "Chicken"}
    >>> lab_contact = create(data)
    >>> lab_contact.getFullname()
    'Lab Chicken'
    >>> api.get_parent(lab_contact)
    <LabContacts at /plone/bika_setup/bika_labcontacts>


Create a Department
~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "Department",
    ...         "parent_path": api.get_path(setup.bika_departments),
    ...         "title": "Microbiology",
    ...         "Manager": api.get_uid(lab_contact)}
    >>> department = create(data)
    >>> department.Title()
    'Microbiology'
    >>> api.get_parent(department)
    <Departments at /plone/bika_setup/bika_departments>

Create an Analysis Category
~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "AnalysisCategory",
    ...         "parent_path": api.get_path(setup.bika_analysiscategories),
    ...         "title": "Microbiology identification",
    ...         "Department": api.get_uid(department)}
    >>> category = create(data)
    >>> category.Title()
    'Microbiology identification'
    >>> api.get_parent(category)
    <AnalysisCategories at /plone/bika_setup/bika_analysiscategories>
    >>> category.getDepartment()
    <Department at /plone/bika_setup/bika_departments/department-1>


Create an Analysis Service
~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "AnalysisService",
    ...         "parent_path": api.get_path(setup.bika_analysisservices),
    ...         "title": "Salmonella",
    ...         "Keyword": "Sal",
    ...         "ScientificName": True,
    ...         "Price": 15,
    ...         "Category": api.get_uid(category),
    ...         "Accredited": True}
    >>> sal = create(data)
    >>> sal.Title()
    'Salmonella'
    >>> sal.getKeyword()
    'Sal'
    >>> sal.getScientificName()
    True
    >>> sal.getAccredited()
    True
    >>> sal.getCategory()
    <AnalysisCategory at /plone/bika_setup/bika_analysiscategories/analysiscategory-1>

    >>> data = {"portal_type": "AnalysisService",
    ...         "parent_path": api.get_path(setup.bika_analysisservices),
    ...         "title": "Escherichia coli",
    ...         "Keyword": "Ecoli",
    ...         "ScientificName": True,
    ...         "Price": 15,
    ...         "Category": api.get_uid(category)}
    >>> ecoli = create(data)
    >>> ecoli.Title()
    'Escherichia coli'
    >>> ecoli.getKeyword()
    'Ecoli'
    >>> ecoli.getScientificName()
    True
    >>> ecoli.getPrice()
    '15.00'
    >>> ecoli.getCategory()
    <AnalysisCategory at /plone/bika_setup/bika_analysiscategories/analysiscategory-1>

Creating a Sample
~~~~~~~~~~~~~~~~~

The creation of a Sample (`AnalysisRequest` portal type) is handled differently
from the rest of objects, an specific function in `senaite.core` must be used
instead of the plone's default creation.

    >>> data = {"portal_type": "AnalysisRequest",
    ...         "parent_uid": api.get_uid(client),
    ...         "Contact": api.get_uid(contact),
    ...         "DateSampled": DateTime().ISO8601(),
    ...         "SampleType": api.get_uid(sample_type),
    ...         "Analyses": map(api.get_uid, [sal, ecoli]) }
    >>> sample = create(data)
    >>> sample
    <AnalysisRequest at /plone/clients/client-7/FE-0001>

    >>> analyses = sample.getAnalyses(full_objects=True)
    >>> sorted(map(lambda an: an.getKeyword(), analyses))
    ['Ecoli', 'Sal']

    >>> sample.getSampleType()
    <SampleType at /plone/bika_setup/bika_sampletypes/sampletype-2>

    >>> sample.getClient()
    <Client at /plone/clients/client-7>

    >>> sample.getContact()
    <Contact at /plone/clients/client-7/contact-1>

Creation restrictions
~~~~~~~~~~~~~~~~~~~~~

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
