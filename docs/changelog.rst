Changelog
=========


2.2.0 (2022-06-10)
------------------

- #47 Use searchable text index converter from catalog API
- #46 Fix ZCTextIndex lookup for custom searchable text query


2.1.0 (2022-01-05)
------------------

- #43 Fix malformed API call


2.0.0 (2021-07-27)
------------------

- Version bump


2.0.0rc2 (2020-10-13)
---------------------

- #41 Added push endpoint for custom jobs


2.0.0rc1 (2020-08-05)
---------------------

- Compatibility with `senaite.core` 2.x


1.2.4 (unreleased)
------------------

- #41 Push endpoint for custom jobs


1.2.3 (2020-08-05)
------------------

- #40 Prevent the id of objects of being accidentally updated
- #40 Do not allow to update objects from setup folder
- #40 Do not allow to update objects from portal root
- #40 Fix upgrade does not work on post-only mode
- #40 Adapter for custom handling of `update` operation
- #37 Do not allow to create objects in setup folder
- #37 Do not allow to create objects in portal root
- #37 Adapter for custom handling of `create` operation
- #37 Make the creation operation to be portal_type-naive
- #35 Added `catalogs` route
- #34 Make senaite.jsonapi catalog-agnostic on searches


1.2.2 (2020-03-03)
------------------

- Missing package data


1.2.1 (2020-03-02)
------------------

- Fixed tests and updated build system


1.2.0 (2018-01-03)
------------------

**Added**

- Added `parent_path` to response data
- Allow custom methods as attributes in adapter

**Removed**

**Changed**

- Integration to SENAITE CORE
- License changed to GPLv2

**Fixed**

- #25 Null values are saved as 'NOW' in Date Time Fields
- Fixed Tests

**Security**


1.1.0 (2017-11-04)
------------------

- Merged PR https://github.com/collective/plone.jsonapi.routes/pull/90
- Get object by UID catalog


1.0.1 (2017-09-30)
------------------

- Fixed broken release (missing MANIFEST.in)


1.0.0 (2017-09-30)
------------------

- First release
