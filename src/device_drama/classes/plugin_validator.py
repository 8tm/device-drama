from enum import Enum
from typing import List

from device_drama.classes.base_plugin import BasePlugin, PluginInfo  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import calendar_version_to_date  # type: ignore


class PluginStatus(Enum):
    COMPATIBLE = 'compatible'
    NEWER = 'newer'
    OLDER = 'older'
    UNKNOWN = 'unknown'


class CompatibilityException(Exception):
    def __init__(self, status: PluginStatus):
        self.status = status


class PluginValidator:
    errors_list: List[str]

    def __init__(self, class_name: type):
        self.errors_list = []
        self.logger = Logger(__name__)
        self.instance = class_name()
        self.class_name = class_name

        self._is_base_plugin_instance()
        self._is_base_plugin_subclass()
        self._subclass_run_method_overrides_base_plugin_run_method()
        self._is_plugin_info_instance()
        self._all_plugins_info_attributes_exists()
        self._all_plugins_attributes_have_proper_values()

    def _is_base_plugin_instance(self) -> None:
        if not isinstance(self.instance, BasePlugin):
            msg = f'"{self.instance}" is not "BasePlugin" instance.'
            self.errors_list.append(msg)
            self.logger.error(msg)

    def _is_base_plugin_subclass(self) -> None:
        if not issubclass(self.class_name, BasePlugin):
            msg = f'"{self.class_name}" is not "BasePlugin" subclass.'
            self.errors_list.append(msg)
            self.logger.error(msg)

    def _subclass_run_method_overrides_base_plugin_run_method(self) -> None:
        if self.class_name.run == BasePlugin.run:  # type: ignore
            msg = f'Missing "run" method in "{self.class_name.__name__}" class.'
            self.errors_list.append(msg)
            self.logger.error(msg)

    def _is_plugin_info_instance(self) -> None:
        if not isinstance(self.instance.info, PluginInfo):
            msg = f'"{self.instance.info}" is not "PluginInfo" instance.'
            self.errors_list.append(msg)
            self.logger.error(msg)

    def _all_plugins_info_attributes_exists(self) -> None:
        plugin_info_attributes = set(
            attr for attr in dir(PluginInfo) if not attr.startswith('__') and not callable(getattr(PluginInfo, attr))
        )
        instance_info_attributes = set(vars(self.instance.info).keys())
        missing_attributes = list(plugin_info_attributes - instance_info_attributes)

        if len(missing_attributes) > 0:
            msg = 'Missing attributes in Plugin from class PluginInfo:'
            self.errors_list.append(msg)
            self.logger.error(msg)
            for missing_attribute in missing_attributes:
                self.logger.error(f'Missing attribute {missing_attribute}')
            self.errors_list.extend([f'- {missing_attribute}' for missing_attribute in missing_attributes])

    def _all_plugins_attributes_have_proper_values(self) -> None:
        for attr, value in vars(self.instance.info).items():
            if not value:
                msg = f'The "{attr}" attribute of the PluginInfo class is empty or None.'
                self.errors_list.append(msg)
                self.logger.error(msg)

    def check_compatibility(self, plugin_version: str, min_version: str, max_version: str) -> PluginStatus:
        created_date = calendar_version_to_date(plugin_version)
        min_date = calendar_version_to_date(min_version)
        max_date = calendar_version_to_date(max_version)
        self.errors_list = []

        if min_date <= created_date <= max_date:
            return PluginStatus.COMPATIBLE
        elif created_date < min_date:
            msg = f'The plugin {self.instance.info.name} is for a older version!'
            self.errors_list.append(msg)
            self.logger.error(msg)
            raise CompatibilityException(PluginStatus.OLDER)

        elif created_date > max_date:
            msg = f'The plugin {self.instance.info.name} is for a newer version!'
            self.errors_list.append(msg)
            self.logger.error(msg)
            raise CompatibilityException(PluginStatus.NEWER)

        return PluginStatus.UNKNOWN

    def validated(self) -> bool:
        status = len(self.errors_list) == 0
        msg = f'Plugin {self.class_name} validated: {status}'
        if status:
            self.logger.info(msg)
        else:
            self.logger.error(msg)
        return status
