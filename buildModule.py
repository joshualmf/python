#!/usr/bin/python
#coding=utf-8

'''
//  buildModule.py
//  build
//
//  Created by Joshua on 2018/1/26.
//
'''

import sys, os, shutil
import getopt


def usage():
    print """
    -h              显示帮助信息
    --project_root  工程目录的绝对路径
    --project_name  工程名，比如：CMBFoundation, Tab1Module
    --git_url       git 仓库的地址
    --branch        git 仓库的分支
    --build_config  构建的配置选项，比如 Debug，Release
    --upload_type   上传的类型，比如library, modulesLib
    """

try:
    options, args = getopt.getopt(sys.argv[1:], "h", ["project_root=", "project_name=", "git_url=", "branch=", "build_config=", "upload_type="])
except getopt.GetoptError:
    print "不支持的参数类型"
    usage()
    sys.exit()

project_root = None
project_name = None
git_url  = None
git_branch  = None
build_config  = None
uploaded_type  = None

for name, value in options:
    if name in ("--project_root"):
        project_root = value
    if name in ("--project_name"):
        project_name = value
    if name in ("--git_url"):
        git_url = value
    if name in ("--branch"):
        git_branch = value
    if name in ("--build_config"):
        build_config = value
    if name in ("--upload_type"):
        uploaded_type = value
    if name in ("-h"):
        usage()
        sys.exit()

for value in (project_root, project_name, git_url, git_branch, build_config, uploaded_type):
    if value == None:
        usage()
        sys.exit()

universal_output_folder = project_root + "/build/" + build_config + "-universal"

def buildModule():
    print "===== 开始build"
    project_file = project_root + "/" + project_name + ".xcodeproj"
    build_dir = project_root + "/build/"
    buildiOSCommand = "xcodebuild -project " + project_file + " -target " + project_name + " -configuration Release ONLY_ACTIVE_ARCH=NO -sdk iphoneos BUILD_DIR=" + build_dir + " clean build"
    buildSimulatorCommand = "xcodebuild -project " + project_file + " -target " + project_name + " -configuration Release ONLY_ACTIVE_ARCH=NO -sdk iphonesimulator BUILD_DIR=" + build_dir + " clean build"
    system(buildiOSCommand)
    system(buildSimulatorCommand)
    combine()

def git_co(git_dir, git_branch):
    git_command = "git fetch; git reset --hard; git clean -fd; git checkout " + git_branch + "; git fetch origin " + git_branch + "; git reset --hard origin/" + git_branch
    os.chdir(git_dir)
    system(git_command)


def combine():
    print "===== build成功， 合并lib以及bundle"

    lib_name = "lib" + project_name + ".a"
    libDevicePath = project_root + "/build/" + build_config + "-iphoneos/" + lib_name 
    libSimulatorPath = project_root + "/build/" + build_config + "-iphonesimulator/" + lib_name 
    output_path = universal_output_folder + "/" + lib_name

    lipo_command = "lipo -create -output " +  output_path + " " + libDevicePath + " " + libSimulatorPath

    if not os.path.isdir(universal_output_folder):
        os.makedirs(universal_output_folder)
    system(lipo_command)

    bundle_path = project_root + "/build/" + build_config + "-iphoneos/" + project_name + "Bundle.bundle"
    
    if os.path.isdir(bundle_path):
        shutil.move(bundle_path, universal_output_folder)

    header_dir = project_root + "/build/" + build_config + "-iphoneos/include/" + project_name
    if os.path.isdir(header_dir):
        shutil.move(header_dir, universal_output_folder)

    upload(universal_output_folder)

def setupProject():
    if not os.path.exists(project_root):
        os.makedirs(project_root)
        system("git clone " + git_url + " " + project_root)
        print "===== git仓库clone成功"

    os.chdir(project_root)
    if os.path.isdir("./build"):
        shutil.rmtree("build")
    git_co(project_root, git_branch)


    library_operation = "rm -rf " + project_root + "/library ; ln -s " + project_root + "/../library " + project_root
    git_co(project_root + "/../library", git_branch)
    system(library_operation)

def upload(ori_dir):
    upload_dir = project_root + "/../" + uploaded_type
    git_co(upload_dir, git_branch) 

    if uploaded_type == 'modulesLib':
        copyToModulesLib(ori_dir, upload_dir)
    elif uploaded_type == 'library':
        copyToLibrary(ori_dir, upload_dir)

    commit_command = 'git add .; git commit -m "iOSBuilder自动构建"; git push origin ' + git_branch
    system(commit_command)

def copyToLibrary(ori_dir, upload_dir):
    thisModule_dir = upload_dir
    lib_name = ori_dir + '/lib' + project_name + '.a'
    bundle_name = ori_dir + '/' + project_name + 'Bundle.bundle'
    header_name = ori_dir + '/' + project_name

    old_lib_name = upload_dir + '/lib' + project_name + '.a'
    old_bundle_name = upload_dir + '/' + project_name + 'Bundle.bundle'
    old_header_name = upload_dir + '/' + project_name

    if os.path.exists(old_lib_name):
        os.remove(old_lib_name)
    shutil.move(lib_name, thisModule_dir)

    if os.path.exists(old_bundle_name):
        shutil.rmtree(old_bundle_name)
    shutil.move(bundle_name, thisModule_dir)

    if os.path.exists(old_header_name):
        shutil.rmtree(old_header_name)
    shutil.move(header_name, thisModule_dir)

def copyToModulesLib(ori_dir, upload_dir):
    thisModule_dir = upload_dir + "/" + project_name
    if os.path.isdir(thisModule_dir):
        shutil.rmtree(thisModule_dir)
    shutil.copytree(ori_dir, thisModule_dir)

def system(cmd):
    status = os.system(cmd)
    if status != 0:
        exit(1)

setupProject()
buildModule()
