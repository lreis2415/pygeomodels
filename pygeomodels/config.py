import os.path
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import AnyStr, List, Optional

import requests
from pygeoc.utils import StringClass

from pygeomodels.utils import is_file_exists


def get_option_value_exactly(cf, secname, optname, valtyp=str):
    # type: (ConfigParser, AnyStr, AnyStr, type) -> Optional[AnyStr, int, float]
    if valtyp == int:
        return cf.getint(secname, optname)
    elif valtyp == float:
        return cf.getfloat(secname, optname)
    elif valtyp == bool:
        return cf.getboolean(secname, optname)
    else:
        return cf.get(secname, optname)


def check_config_option(cf, secname, optnames, print_warn=False):
    # type: (ConfigParser, AnyStr, Optional[AnyStr, List[AnyStr]], bool) -> (bool, AnyStr, AnyStr)
    if not isinstance(cf, ConfigParser):
        raise IOError(
            "ErrorInput: The first argument cf MUST be the object of `ConfigParser`!"
        )
    if type(optnames) is not list:
        optnames = [optnames]  # type: List[AnyStr]

    if secname not in cf.sections():
        if print_warn:
            print(
                "Warning: Section %s is NOT defined, try to find in DEFAULT section!"
                % secname
            )
        for optname in optnames:  # For backward compatibility
            if cf.has_option("", optname):  # May be in [DEFAULT] section
                return True, "", optname
        if print_warn:
            print(
                "Warning: Section %s is NOT defined, "
                "Option %s is NOT FOUND!" % (secname, ",".join(optnames))
            )
        return False, "", ""
    else:
        for optname in optnames:  # For backward compatibility
            if cf.has_option(secname, optname):
                return True, secname, optname
        if print_warn:
            print(
                "Warning: Option %s is NOT FOUND in Section %s!"
                % (",".join(optnames), secname)
            )
        return False, "", ""


def get_option_value(
    cf,  # type: ConfigParser
    secname,  # type: AnyStr
    optnames,  # type: Optional[AnyStr, List[AnyStr]]
    valtyp=str,  # type: Optional[AnyStr, int, float, bool]
    defvalue="",  # type: Optional[AnyStr, int, float, bool]
    required=True,  # type: bool
    print_warn=False,  # type: bool
):  # type: (...) -> Optional[AnyStr, int, float]
    found, sname, oname = check_config_option(
        cf, secname, optnames, print_warn=print_warn
    )
    if not found:
        if required:
            raise IOError("Error Input in configuration!")
        else:
            if defvalue == "" and (valtyp == int or valtyp == float):
                return (
                    -9999
                )  # int or float value type, but not set default value properly
            return defvalue
    return get_option_value_exactly(cf, sname, oname, valtyp=valtyp)


def get_option_list(
    cf,  # type: ConfigParser
    secname,  # type: AnyStr
    optnames,  # type: Optional[AnyStr, List[AnyStr]]
    valtyp=str,  # type: Optional[AnyStr, int, float, bool]
    defvalue="",  # type: Optional[AnyStr, int, float, bool]
    required=True,  # type: bool
    print_warn=False,  # type: bool
):  # type: (...) -> List[Optional[AnyStr, int, float]]
    found, sname, oname = check_config_option(
        cf, secname, optnames, print_warn=print_warn
    )
    if not found:
        if required:
            raise IOError("Error Input in configuration!")
        else:
            if defvalue == "" and (valtyp == int or valtyp == float):
                return [
                    -9999
                ]  # int or float value type, but not set default value properly
            return [defvalue]
    strvalue = get_option_value_exactly(cf, sname, oname, valtyp=str)
    if valtyp == str:
        return StringClass.split_string(strvalue, ",", elim_empty=True)
    else:
        return StringClass.extract_numeric_values_from_string(strvalue)


class ModelEngineConfig(object):
    """Parse Model Engine configurations."""

    def __init__(self, cf):  # type: (ConfigParser) -> None
        """Initialization."""
        # Authorization related
        auth = "AUTH"
        if auth not in cf.sections():
            raise ValueError("[AUTH] section MUST be existed in *.ini file.")
        self.usernames = get_option_list(cf, auth, "usernames")
        self.passwords = get_option_list(cf, auth, "passwords")
        if len(self.usernames) != len(self.passwords):
            raise ValueError(
                "usernames and passwords in the [AUTH] section MUST have the same count!"
            )
        if len(self.usernames) < 1:
            raise ValueError("usernames in the [AUTH] section MUST have at least one!")
        self.keycloak_url = get_option_value(cf, auth, "keycloak_url")
        self.realm_name = get_option_value(cf, auth, "realm_name")
        self.client_id = get_option_value(cf, auth, "client_id")
        self.client_secret_key = get_option_value(cf, auth, "client_secret_key")

        # Services related
        service = "SERVICE"
        if service not in cf.sections():
            raise ValueError("[SERVICE] section MUST be existed in *.ini file.")
        self.modelmanager_url = get_option_value(cf, service, "modelmanager_url")
        self.api_basename = get_option_value(cf, service, "api_basename")
        # APIs of model management
        self.api_cls_modelmanager = get_option_value(
            cf, service, "api_cls_modelmanager"
        )
        # modelmanager_url/api_basename/api_cls_modelmanager/api_mgt_generalmodel/
        self.api_mgt_generalmodel = get_option_value(
            cf, service, "api_mgt_generalmodel"
        )
        self.api_gm_catalog = get_option_value(cf, service, "api_gm_catalog")
        self.api_gm_catalogcls = get_option_value(cf, service, "api_gm_catalogcls")
        self.api_gm_catalogappl = get_option_value(cf, service, "api_gm_catalogappl")

        # API版本控制
        self.api_version_gm_catalog = get_option_value(
            cf,
            service,
            "api_version_gm_catalog",
            valtyp=str,
            defvalue="",
            required=False,
        )
        self.api_version_sm_list = get_option_value(
            cf, service, "api_version_sm_list", valtyp=str, defvalue="", required=False
        )
        self.api_version_sm_ui = get_option_value(
            cf, service, "api_version_sm_ui", valtyp=str, defvalue="", required=False
        )
        # Catalog root node ID for v2 API
        self.api_gm_catalog_root_id = get_option_value(
            cf,
            service,
            "api_gm_catalog_root_id",
            valtyp=str,
            defvalue="modelbank",
            required=False,
        )

        # modelmanager_url/api_basename/api_cls_modelmanager/api_mgt_generalmodel/
        self.api_mgt_singlemodel = get_option_value(cf, service, "api_mgt_singlemodel")
        self.api_sm_list = get_option_value(cf, service, "api_sm_list")
        # modelmanager_url/api_basename/api_cls_modelmanager/api_mgt_generalmodel/{id}/
        self.api_sm_info = get_option_value(cf, service, "api_sm_info")
        self.api_sm_ui = get_option_value(cf, service, "api_sm_ui")

        # APIs of model runner
        self.api_cls_runner = get_option_value(cf, service, "api_cls_runner")
        # modelmanager_url/api_basename/api_cls_runner/api_run_singlemodel/{id}/
        self.api_run_singlemodel = get_option_value(cf, service, "api_run_singlemodel")
        self.api_srun_run = get_option_value(cf, service, "api_srun_run")
        # modelmanager_url/api_basename/api_cls_runner/api_run_singlemodel/api_srun_task/{taskId}/
        self.api_srun_task = get_option_value(cf, service, "api_srun_task")
        self.api_srunt_stop = get_option_value(cf, service, "api_srunt_stop")
        self.api_srunt_del = get_option_value(cf, service, "api_srunt_del")
        self.api_srunt_info = get_option_value(cf, service, "api_srunt_info")
        self.api_srunt_log = get_option_value(cf, service, "api_srunt_log")

        # APIs of user project
        self.api_cls_usrprj = get_option_value(cf, service, "api_cls_usrprj")
        # modelmanager_url/api_basename/api_cls_usrprj/api_uprj_list
        self.api_uprj_list = get_option_value(cf, service, "api_uprj_list")
        # modelmanager_url/api_basename/api_cls_usrprj/{id}/
        self.api_uprj_data = get_option_value(cf, service, "api_uprj_data")
        self.api_uprj_log = get_option_value(cf, service, "api_uprj_log")
        self.api_uprj_detail = get_option_value(cf, service, "api_uprj_detail")
        self.api_uprj_prog = get_option_value(cf, service, "api_uprj_prog")
        self.api_uprj_stop = get_option_value(cf, service, "api_uprj_stop")
        self.api_uprj_del = get_option_value(cf, service, "api_uprj_del")
        # modelmanager_url/api_basename/api_cls_usrprj/api_uprj_single/{id}/
        self.api_uprj_single = get_option_value(cf, service, "api_uprj_single")
        self.api_sprj_run = get_option_value(cf, service, "api_sprj_run")

        # APIs of AOI (study area)
        self.aoi_list_data_path = get_option_value(
            cf, service, "aoi_list_data_path", valtyp=str, defvalue="", required=False
        )
        self.mcp_output_root = get_option_value(
            cf,
            service,
            "mcp_output_root",
            valtyp=str,
            defvalue="job_results",
            required=False,
        )

        # Feature flags related
        feature_flags = "FEATURE_FLAGS"
        if feature_flags in cf.sections():
            self.enable_terrain_analysis_tools = get_option_value(
                cf,
                feature_flags,
                "enable_terrain_analysis_tools",
                valtyp=bool,
                defvalue=False,
                required=False,
            )
            self.enable_model_management_tools = get_option_value(
                cf,
                feature_flags,
                "enable_model_management_tools",
                valtyp=bool,
                defvalue=True,
                required=False,
            )
            self.enable_aoi_tools = get_option_value(
                cf,
                feature_flags,
                "enable_aoi_tools",
                valtyp=bool,
                defvalue=False,
                required=False,
            )
            # Test token for local development
            self.test_bearer_token = get_option_value(
                cf,
                feature_flags,
                "test_bearer_token",
                valtyp=str,
                defvalue="",
                required=False,
            )
        else:
            # Default values for backward compatibility
            self.enable_terrain_analysis_tools = False
            self.enable_model_management_tools = True
            self.enable_aoi_tools = False
            self.test_bearer_token = ""

        self.token = self.Token

    def get_api_base(self, version_override: str = "") -> str:
        """
        Get API base path with version.

        Args:
            version_override: Specific version to use (e.g., 'v2').
                            If empty, uses default from api_basename.

        Returns:
            Base path like 'mbms/v1' or 'mbms/v2'
        """
        if version_override:
            return f"mbms/{version_override}"
        return self.api_basename

    def build_api_path(self, *path_parts: str, version_key: str = "") -> str:
        """
        Build complete API path with automatic version selection.

        Args:
            *path_parts: Path components to join
            version_key: Configuration key for version override (e.g., 'gm_catalog')

        Returns:
            Complete API path

        Example:
            # Uses default v1
            cfg.build_api_path('model-manager', 'general-models', 'catalog')
            # Returns: 'mbms/v1/model-manager/general-models/catalog'

            # Uses v2 if api_version_gm_catalog is configured
            cfg.build_api_path('model-manager', 'general-models', 'catalog', version_key='gm_catalog')
            # Returns: 'mbms/v2/model-manager/general-models/catalog'
        """
        version_override = ""
        if version_key:
            version_override = getattr(self, f"api_version_{version_key}", "")

        base = self.get_api_base(version_override)
        return f"{base}/{'/'.join(path_parts)}"

    @property
    def Token(self, uidx=0):
        """Get the 'access token' from Keycloak.
        If successful we'll get the token (a big long string)
        """
        self.token = "default_token"
        return self.token

        realm_url: str = f"{self.keycloak_url}/realms/{self.realm_name}"
        url = f"{realm_url}/protocol/openid-connect/token"
        data = (
            f"client_id={self.client_id}"
            f"&grant_type=password"
            f"&username={self.usernames[uidx]}"
            f"&password={self.passwords[uidx]}"
            f"&client_secret={self.client_secret_key}"
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(url, headers=headers, data=data, timeout=4.0)
        if resp.status_code == 200:
            try:
                if "access_token" in resp.json():
                    self.token = resp.json()["access_token"]
            except:
                self.token = ""
        return self.token


def parse_config(cfg_file="", case_sensitive=False):
    # type: (AnyStr, bool) -> ModelEngineConfig
    """Load and parse model engine configuration from *.ini file.

    Args:
        cfg_file: INI configuration file.
        case_sensitive: True means preserve case-sensitive in ConfigParser.
                        https://stackoverflow.com/a/1611877/4837280
    """
    cf = ConfigParser()
    if case_sensitive:
        cf.optionxform = str
    if cfg_file == "":
        # Priority: local_config.ini > default_config.ini
        local_cfg = Path(__file__).with_name("local_config.ini")
        default_cfg = Path(__file__).with_name("default_config.ini")

        # Always read default config first as base
        if default_cfg.exists():
            cfg_file = default_cfg
            cf.read(cfg_file)
        else:
            print("Default configuration file not found!")
            sys.exit()

        # Then overlay local config if it exists
        if local_cfg.exists():
            cf.read(local_cfg)
            cfg_file = local_cfg  # For error messages

    else:
        # User specified config file
        cfg_file = os.path.abspath(cfg_file)
        if not is_file_exists(cfg_file):
            print("The specific configuration file did not exist!")
            sys.exit()
        cf.read(cfg_file)

    return ModelEngineConfig(cf)


if __name__ == "__main__":
    cfg = parse_config()
    print(cfg.keycloak_url)
