class HiPuterError(Exception):
    """Base error shown as a clean CLI message."""


class ConfigError(HiPuterError): pass
class ModelError(HiPuterError): pass
class AudioError(HiPuterError): pass
class ActionError(HiPuterError): pass
class UnsupportedAction(ActionError): pass
class LifecycleError(HiPuterError): pass
