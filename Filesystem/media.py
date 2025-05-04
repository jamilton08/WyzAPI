import os
from wyzcon.settings import MEDIA_ROOT as root, STATIC_URL
from django.core.exceptions import MultipleObjectsReturned

class OrgFileDirect(object

    def generate_random_name():
         from django.utils.crypto import get_random_string
         unique_id = get_random_string(length=32)
         unique_id

    def _verify_parent(self, parent_folder):
        full_path = os.path.join(root,parent_folder)
        if  os.path.isdir(full_path) is False:
            os.mkdir(full_path)
        return parent_folder

    def _verify_subparent(self, parent_folder, org):
        path = self._verify_parent(parent_folder = parent_folder)
        sub_folder = org.name + parent_folder
        full_path = os.path.join(root, path, sub_folder)
        if os.path.isdir(full_path) is False:
            os.mkdir(full_path)
        return  os.path.join(path, sub_folder)

    def _post_handler(self, file_kind, filename, instance):
        #decided by organization_user
        org_user = instance.org_user if hasattr(instance, 'org_user') else instance.owner.organization_user
        org = org_user.organization
        path_name = os.path.join(self._verify_subparent(parent_folder = file_kind,
                                                org = org), org_user.user.username)
        return '%s/%s' % (path_name, filename)

    def _instance_route(self, instance, filename):
        name = instance.__class__.__name__
        if name== "OrgBucket":
            instance_kind = 'org_photos'
        elif name ==  "Profile":
            instance_kind = 'profile_pic'
        elif name == "OrgProfile":
            instance_kind = 'org_profile_pics'
        return self._post_handler(instance_kind, filename, instance )

    def file_saver(self, instance,filename):
        return self._instance_route(instance = instance, filename = filename)

class UserFileDirect(object):

    def _verify_parent(self, parent_folder):
        full_path = os.path.join(root,parent_folder)
        if  os.path.isdir(full_path) is False:
            os.mkdir(full_path)
        return parent_folder

    def _verify_subparent(self, parent_folder):
        path = self._verify_parent(parent_folder = parent_folder)
        sub_folder =  parent_folder
        full_path = os.path.join(root, path, sub_folder)
        if os.path.isdir(full_path) is False:
            os.mkdir(full_path)
        return  os.path.join(path, sub_folder)

    def _post_handler(self, file_kind, filename, instance):
        user = instance.user
        path_name = os.path.join(self._verify_subparent(parent_folder = file_kind), user.username)
        return '%s/%s' % (path_name, filename)

    def _instance_route(self, instance, filename):
        name = instance.__class__.__name__
        if name == "Profile":
            instance_kind = 'profile_pic'
        elif name== "Pictures":
            instance_kind = 'photos'
        elif name == "Post":
            instance_kind = 'post'
        elif name == "PhotoBucket":
            instance_kind = "user_photos"
        return self._post_handler(instance_kind, filename, instance )

    def file_saver(self, instance,filename):
        return self._instance_route(instance = instance, filename = filename)
