# DjangoFactory Feature Coverage

## Implemented
- Built-in field annotations for core Django fields (auto/bigint/bool/char/url/date/datetime/decimal/duration/filepath/etc.)
- Faker providers for email, URL, file path
- Literal inference for fields with `choices`
- Sync persistence via `DjangoSyncPersistence`
- Async persistence explicitly disabled
- Constraint extraction: `max_length`, `decimal_places`, `max_digits`, slug pattern
- Test utilities for temporary model setup

## Missing / Planned
- Support for all remaining Django field types (UUID, JSON, IP, time, CIChar, array/geo)
- Relation handling for `ForeignKey`, `OneToOneField`, `ManyToManyField`
- Respecting `unique`, `unique_together`, and custom validators
- Handling defaults (`auto_now`, callable defaults) and `choices` on non-char fields
- Persistence ordering and transaction management
- pytest-django integration helpers
- Settings-aware configuration (`AUTH_USER_MODEL`, storage backends, time zone)
- Extension registry for custom/third-party fields
- Comprehensive docs and recipes for common Django patterns
