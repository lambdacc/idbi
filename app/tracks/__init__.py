"""CreditPulse track packages. Each track is self-contained and isolated: a
track may import platform core but never another track (enforced by the isolation
linter in app/tests). Deleting a track folder leaves the platform fully working.
"""
