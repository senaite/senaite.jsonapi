UID REFERENCES
--------------

Setting a reference to another object through the field managers.

A single valued field is the interesting case, because the two field
implementations want the value in different shapes and both validate
before they store. An Archetypes UIDReferenceField refuses a list with
"[...] is not supported". A Dexterity UIDReferenceField derives from
`zope.schema.List` and refuses a bare UID with WrongType.

The payload is sent as JSON here, which is what makes the UIDs unicode:
a value that reaches the field unconverted fails its ASCIILine value
type, and the object is then refused on the whole-object validation
rather than where the value went in.

Running this test from the buildout directory:

    bin/test test_doctests -t uidreferences


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID

    >>> from bika.lims import api

Functional Helpers:

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, json.dumps(data), "application/json")
    ...     return browser.contents

    >>> def get_item_object(response):
    ...     items = json.loads(response).get("items")
    ...     assert(len(items) == 1)
    ...     return api.get_object(items[0]["uid"])

    >>> def create(data):
    ...     return get_item_object(post("create", data))

    >>> def update(data):
    ...     return get_item_object(post("update", data))

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setup = portal.setup
    >>> bika_setup = portal.bika_setup
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Something to point at:

    >>> data = {"portal_type": "LabContact",
    ...         "parent_path": api.get_path(bika_setup.bika_labcontacts),
    ...         "Firstname": "Anna",
    ...         "Surname": "Meyer"}
    >>> contact = create(data)

    >>> data = {"portal_type": "Department",
    ...         "parent_path": api.get_path(setup.departments),
    ...         "title": "Chemistry",
    ...         "department_id": "CHEM",
    ...         "manager": api.get_uid(contact)}
    >>> department = create(data)


A single valued Dexterity reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An analysis category names one responsible department, and the field is
declared `multi_valued=False`:

    >>> data = {"portal_type": "AnalysisCategory",
    ...         "parent_path": api.get_path(setup.analysiscategories),
    ...         "title": "Water Chemistry",
    ...         "department": api.get_uid(department)}
    >>> category = create(data)
    >>> api.get_uid(category.getDepartment()) == api.get_uid(department)
    True

The stored UID is a native string, which is what the field's ASCIILine
value type accepts:

    >>> from senaite.core.content.analysiscategory import (
    ...     IAnalysisCategorySchema)
    >>> field = IAnalysisCategorySchema["department"]
    >>> isinstance(field.get_raw(category), str)
    True

The same through the BBB name the type kept from its Archetypes days.
It has to end up in the same shape, because the object is validated as
a whole afterwards:

    >>> data = {"portal_type": "AnalysisCategory",
    ...         "parent_path": api.get_path(setup.analysiscategories),
    ...         "title": "Microbiology",
    ...         "Department": api.get_uid(department)}
    >>> category2 = create(data)
    >>> isinstance(field.get_raw(category2), str)
    True

A BBB name of more than one word has to reach the field as well. The
schema names it in snake case, so `RetentionPeriod` has to find
`retention_period` rather than `retentionPeriod`. That field is a
duration, which only its field manager knows how to build out of the
mapping JSON can carry:

    >>> data = {"portal_type": "SamplePoint",
    ...         "parent_path": api.get_path(setup.samplepoints),
    ...         "title": "Reservoir inlet",
    ...         "SamplingFrequency": {"days": 7}}
    >>> sample_point = create(data)
    >>> sample_point.sampling_frequency
    datetime.timedelta(7)

A list of one is accepted as well:

    >>> data = {"uid": api.get_uid(category2),
    ...         "department": [api.get_uid(department)]}
    >>> category2 = update(data)
    >>> api.get_uid(category2.getDepartment()) == api.get_uid(department)
    True

More than one is refused, because the field holds a single reference:

    >>> data = {"portal_type": "Department",
    ...         "parent_path": api.get_path(setup.departments),
    ...         "title": "Microbiology",
    ...         "department_id": "MICRO",
    ...         "manager": api.get_uid(contact)}
    >>> other = create(data)

    >>> data = {"uid": api.get_uid(category2),
    ...         "department": [api.get_uid(department), api.get_uid(other)]}
    >>> category2 = update(data)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 400: Bad Request


A name that is no field at all
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A BBB name is a name the type supports, and it reaches the field. A
name that reaches nothing is a mistake, and saying so is the whole
point of the two being told apart:

    >>> browser.raiseHttpErrors = False
    >>> print(post("create", {
    ...     "portal_type": "AnalysisProfile",
    ...     "parent_path": api.get_path(setup.analysisprofiles),
    ...     "title": "Typo Panel",
    ...     "Service": []}))
    {...No field named 'Service' on AnalysisProfile. Did you mean 'services'?...}

Without a field close enough to suggest, it says only what it knows:

    >>> print(post("create", {
    ...     "portal_type": "AnalysisProfile",
    ...     "parent_path": api.get_path(setup.analysisprofiles),
    ...     "title": "Typo Panel",
    ...     "Nonsense": 42}))
    {...No field named 'Nonsense' on AnalysisProfile...}

    >>> browser.raiseHttpErrors = True


A single valued Archetypes reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An analysis service points at one default method, and that field is an
Archetypes UIDReferenceField, which wants the UID itself:

    >>> data = {"portal_type": "Method",
    ...         "parent_path": api.get_path(setup.methods),
    ...         "title": "Photometric Determination"}
    >>> method = create(data)

    >>> data = {"portal_type": "AnalysisService",
    ...         "parent_path": api.get_path(bika_setup.bika_analysisservices),
    ...         "title": "Nitrate",
    ...         "Keyword": "NO3",
    ...         "Category": api.get_uid(category),
    ...         "Methods": [api.get_uid(method)],
    ...         "Method": api.get_uid(method)}
    >>> service = create(data)
    >>> api.get_uid(service.getMethod()) == api.get_uid(method)
    True
