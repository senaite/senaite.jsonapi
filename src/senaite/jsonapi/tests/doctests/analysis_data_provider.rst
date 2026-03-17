ANALYSIS DATA PROVIDER
----------------------

Running this test from the buildout directory:

    bin/test test_doctests -t analysis_data_provider


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from DateTime import DateTime
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from bika.lims import api

Functional Helpers:

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


Create test data
~~~~~~~~~~~~~~~~

Create the required setup objects:

    >>> client = create({
    ...     "portal_type": "Client",
    ...     "parent_path": api.get_path(portal.clients),
    ...     "title": "Test Client",
    ...     "ClientID": "TC"})

    >>> contact = create({
    ...     "portal_type": "Contact",
    ...     "parent_path": api.get_path(client),
    ...     "Firstname": "Jane",
    ...     "Surname": "Doe"})

    >>> sample_type = create({
    ...     "portal_type": "SampleType",
    ...     "parent_path": api.get_path(portal.setup.sampletypes),
    ...     "title": "Water",
    ...     "MinimumVolume": "100 ml",
    ...     "Prefix": "WA"})

    >>> lab_contact = create({
    ...     "portal_type": "LabContact",
    ...     "parent_path": api.get_path(setup.bika_labcontacts),
    ...     "Firstname": "Lab",
    ...     "Surname": "Manager"})

    >>> department = create({
    ...     "portal_type": "Department",
    ...     "DepartmentID": "CH",
    ...     "parent_path": api.get_path(portal.setup.departments),
    ...     "title": "Chemistry",
    ...     "Manager": api.get_uid(lab_contact)})

    >>> category = create({
    ...     "portal_type": "AnalysisCategory",
    ...     "parent_path": api.get_path(portal.setup.analysiscategories),
    ...     "title": "Metals",
    ...     "Department": api.get_uid(department)})

    >>> service = create({
    ...     "portal_type": "AnalysisService",
    ...     "parent_path": api.get_path(setup.bika_analysisservices),
    ...     "title": "Calcium",
    ...     "Keyword": "Ca",
    ...     "Price": 10,
    ...     "Category": api.get_uid(category)})

Create a Sample with one analysis:

    >>> sample = create({
    ...     "portal_type": "AnalysisRequest",
    ...     "parent_uid": api.get_uid(client),
    ...     "Contact": api.get_uid(contact),
    ...     "DateSampled": DateTime().ISO8601(),
    ...     "SampleType": api.get_uid(sample_type),
    ...     "Analyses": [api.get_uid(service)]})

    >>> analyses = sample.getAnalyses(full_objects=True)
    >>> len(analyses)
    1

    >>> analysis = analyses[0]
    >>> analysis_uid = api.get_uid(analysis)


Analysis fields via the API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When fetching an analysis with ``complete=1``, the response includes the
computed fields ``getFormattedResult`` and ``isRetest`` injected by the
``AnalysisDataProvider``:

    >>> response = get("analysis/{}?complete=1".format(analysis_uid))
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> len(items)
    1

    >>> item = items[0]

The ``getFormattedResult`` field is present.  Since no result has been
submitted yet, it returns an empty string:

    >>> "getFormattedResult" in item
    True
    >>> item["getFormattedResult"]
    u''

The ``isRetest`` field is present and ``False`` for a regular analysis:

    >>> "isRetest" in item
    True
    >>> item["isRetest"]
    False


Formatted result after submitting a value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Receive the sample and submit a result for the analysis:

    >>> from bika.lims.workflow import doActionFor as do_action_for
    >>> transitioned = do_action_for(sample, "receive")
    >>> analysis.setResult("42")
    >>> transaction.commit()

The formatted result now reflects the submitted value:

    >>> response = get("analysis/{}?complete=1".format(analysis_uid))
    >>> data = json.loads(response)
    >>> item = data["items"][0]
    >>> item["getFormattedResult"]
    u'42'
    >>> item["isRetest"]
    False


Formatted result with ResultOptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a service with predefined result options (select type):

    >>> service_ro = create({
    ...     "portal_type": "AnalysisService",
    ...     "parent_path": api.get_path(setup.bika_analysisservices),
    ...     "title": "Color",
    ...     "Keyword": "Color",
    ...     "Price": 5,
    ...     "Category": api.get_uid(category)})

    >>> options = [
    ...     {"ResultValue": "0", "ResultText": "Colorless"},
    ...     {"ResultValue": "1", "ResultText": "Yellow"},
    ...     {"ResultValue": "2", "ResultText": "Brown"},
    ... ]
    >>> service_ro.setResultOptions(options)
    >>> service_ro.setResultType("select")
    >>> transaction.commit()

Create a sample with this service:

    >>> sample2 = create({
    ...     "portal_type": "AnalysisRequest",
    ...     "parent_uid": api.get_uid(client),
    ...     "Contact": api.get_uid(contact),
    ...     "DateSampled": DateTime().ISO8601(),
    ...     "SampleType": api.get_uid(sample_type),
    ...     "Analyses": [api.get_uid(service_ro)]})

    >>> analyses2 = sample2.getAnalyses(full_objects=True)
    >>> an_color = analyses2[0]
    >>> an_color_uid = api.get_uid(an_color)

Receive the sample and set a result using one of the option values:

    >>> transitioned = do_action_for(sample2, "receive")
    >>> an_color.setResult("1")
    >>> transaction.commit()

The formatted result returns the display text, not the raw value:

    >>> response = get("analysis/{}?complete=1".format(an_color_uid))
    >>> data = json.loads(response)
    >>> item = data["items"][0]
    >>> item["getFormattedResult"]
    u'Yellow'
    >>> item["isRetest"]
    False


Retest analysis
~~~~~~~~~~~~~~~

Submit the first analysis and then retract it to create a retest:

    >>> transitioned = do_action_for(analysis, "submit")
    >>> transitioned = do_action_for(analysis, "retract")
    >>> transaction.commit()

The retracted analysis now has a retest.  Fetch the retest:

    >>> retest = analysis.getRetest()
    >>> retest_uid = api.get_uid(retest)

The retest is flagged as such via the API:

    >>> response = get("analysis/{}?complete=1".format(retest_uid))
    >>> data = json.loads(response)
    >>> item = data["items"][0]
    >>> item["isRetest"]
    True

The original retracted analysis is not a retest:

    >>> response = get("analysis/{}?complete=1".format(analysis_uid))
    >>> data = json.loads(response)
    >>> item = data["items"][0]
    >>> item["isRetest"]
    False
