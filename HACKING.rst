networking-opencontrail Style Commandments
===============================================

Read the OpenStack Style Commandments http://docs.openstack.org/developer/hacking/

networking-opencontrail Specific Commandments
---------------------------------------------

- [N322] Detect common errors with assert_called_once_with
- [N328] Detect wrong usage with assertEqual
- [N330] Use assertEqual(*empty*, observed) instead of
         assertEqual(observed, *empty*)
- [N331] Detect wrong usage with assertTrue(isinstance()).
- [N332] Use assertEqual(expected_http_code, observed_http_code) instead of
         assertEqual(observed_http_code, expected_http_code).
- [N334] Use unittest2 uniformly across Neutron.
- [N343] Production code must not import from neutron.tests.*
- [N344] Python 3: Do not use filter(lambda obj: test(obj), data). Replace it
  with [obj for obj in data if test(obj)].
- [N524] Prevent use of deprecated contextlib.nested.
- [N525] Python 3: Do not use xrange.
- [N526] Python 3: do not use basestring.
- [N527] Python 3: do not use dict.iteritems.
- [N529] Method's default argument shouldn't be mutable
- [N532] Validate that LOG.warning is used instead of LOG.warn. The latter is deprecated.
- [N535] Usage of Python eventlet module not allowed
- [N536] Use assertIsNone/assertIsNotNone rather than assertEqual/assertIs to check None values.
- [N537] Don't translate logs.
