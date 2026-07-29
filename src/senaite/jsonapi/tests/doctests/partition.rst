PARTITION
---------

The partition operation creates aliquots of a received sample, moving the
selected analyses into the new partition.

Running this test from the buildout directory:

    bin/test test_doctests -t partition


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from DateTime import DateTime
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID

    >>> from bika.lims import api
    >>> from bika.lims.utils.analysisrequest import create_analysisrequest

Functional Helpers:

    >>> def post_json(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, json.dumps(data), "application/json")
    ...     return browser.contents

Variables:

    >>> portal = self.portal
    >>> request = self.request
    >>> setup = portal.setup
    >>> bika_setup = portal.bika_setup
    >>> api_url = "{}/@@API/senaite/v1".format(portal.absolute_url())
    >>> browser = self.getBrowser()
    >>> date_now = DateTime().strftime("%Y-%m-%d")
    >>> setRoles(portal, TEST_USER_ID, ["Manager", "LabManager"])
    >>> transaction.commit()

Create the required setup content and a primary sample:

    >>> clients = portal.clients
    >>> client = api.create(clients, "Client", Name="ACME", ClientID="A")
    >>> contact = api.create(client, "Contact", Firstname="John",
    ...                      Surname="Doe")
    >>> sampletype = api.create(setup.sampletypes, "SampleType",
    ...                         Prefix="water", MinimumVolume="100 ml")
    >>> category = api.create(setup.analysiscategories, "AnalysisCategory",
    ...                       title="Water")
    >>> service = api.create(bika_setup.bika_analysisservices,
    ...                      "AnalysisService", title="PH", ShortTitle="ph",
    ...                      Category=category, Keyword="PH")
    >>> values = {
    ...     "Client": client.UID(),
    ...     "Contact": contact.UID(),
    ...     "SamplingDate": date_now,
    ...     "DateSampled": date_now,
    ...     "SampleType": sampletype.UID(),
    ... }
    >>> sample = create_analysisrequest(client, request, values,
    ...                                 [service.UID()])
    >>> transaction.commit()


Create a partition
~~~~~~~~~~~~~~~~~~~

    >>> analyses = [api.get_uid(an)
    ...             for an in sample.getAnalyses(full_objects=True)]
    >>> data = {"uid": api.get_uid(sample), "analyses": analyses}
    >>> response = post_json("partition", data)
    >>> result = json.loads(response)
    >>> result["count"]
    1

The new partition points back to the primary sample:

    >>> partition = api.get_object(result["items"][0]["uid"])
    >>> primary = partition.getParentAnalysisRequest()
    >>> api.get_uid(primary) == api.get_uid(sample)
    True


Detach, reattach and publish
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only *creating* a partition needs a dedicated endpoint, because it takes
parameters (which analyses, sample type, container). The rest of the
partition lifecycle are plain workflow transitions, so they go through the
standard update route with the `transition` key (see the UPDATE doctest for
the mechanism):

Detach a partition (it then behaves like a primary sample and carries the
`IDetachedPartition` marker)::

    POST update {"uid": "<partition uid>", "transition": "detach"}

Reattach it to its original primary sample::

    POST update {"uid": "<partition uid>", "transition": "reattach"}

Publish a verified sample::

    POST update {"uid": "<verified sample uid>", "transition": "publish"}


Multiple partitions in one call
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> data = {"uid": api.get_uid(sample),
    ...         "partitions": [{"analyses": []}, {"analyses": []}]}
    >>> response = post_json("partition", data)
    >>> json.loads(response)["count"]
    2


Errors
~~~~~~

A missing primary uid is rejected:

    >>> post_json("partition", {"analyses": []})
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 400: Bad Request

An unknown primary uid returns a 404:

    >>> post_json("partition", {"uid": "no-such-uid"})
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 404: Not Found
