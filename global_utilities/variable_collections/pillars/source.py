from importlib import import_module as _i

SESSION = _i("session.models").SessionsContainer
ORGANIZATION = _i("organizations.models").Organization
#ORGANIZATIONUSER = _i("organizations.models").OrganizationUser
WYZDATE = _i("tiempo.models").WyzDateModel
WYZTIME = _i("tiempo.models").WyzTimeModel
WYZFLOAT = _i("tiempo.models").WyzFloatModel
SERVICES = _i("services.models").ServicesContainer
ATTENDANCE = _i("attendance.models").Attn
