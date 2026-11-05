**Merge checklist:**
- [ ] Any new requirements are in the right place in `pyproject.toml` (do **not** manually modify `uv.lock`)
    - `[project].dependencies` if needed in production but edx-analytics-data-api doesn't install it
    - the `test` dependency group if edx-analytics-data-api pins it, with a matching version
    - `make upgrade` has been run to regenerate `uv.lock`
- [ ] `make static` has been run to update webpack bundling if any static content was updated
- [ ] `./manage.py makemigrations` has been run
    - Checkout the [Database Migration](https://openedx.atlassian.net/wiki/spaces/AC/pages/23003228/Everything+About+Database+Migrations) Confluence page for helpful tips on creating migrations.
    - *Note*: This **must** be run if you modified any models.
      - It may or may not make a migration depending on exactly what you modified, but it should still be run.
    - This should be run from either a venv with all the edx-analytics-data-api requirements installed or if you checked out edx-enterprise-data into the src directory used by edx-analytics-data-api, you can run this command through an edx-analytics-data-api shell.
        - It would be `./manage.py makemigrations` in the shell.
- [ ] Translations updated (see docs/internationalization.rst but also this isn't blocking for merge atm)

**Post merge:**
- [ ] PR created in [edx-analytics-data-api](https://github.com/openedx/edx-analytics-data-api) to upgrade dependencies (including edx-enterprise-data)
    - This **must** be done after the version is visible in PyPi as `make upgrade` in edx-analytics-data-api will look for the latest version in PyPi.
    - Note: the edx-enterprise-data constraint in edx-analytics-data-api **must** also be bumped to the latest version in PyPi.
