Here are the steps on how to make a new release.

1. Create a ``release-<VERSION>`` branch from ``upstream/master``.
2. Update ``CHANGELOG.rst``.
3. Push a branch with the changes to ``upstream``.
4. Once all builds pass, push a tag to ``upstream`` in the format ``v<VERSION>``.
5. Merge the PR.
