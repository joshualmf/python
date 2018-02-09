#!/usr/bin/python
#coding=utf-8

'''
//  buildMain.py
//  build
//
//  Created by Joshua on 2017/1/26.
//
'''

import sys, os, shutil, time, urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import biplist

import getopt


def usage():
    print """
    -h                  显示帮助信息
    --project_root      工程目录的绝对路径
    --project_file      工程名，绝对路径
    --target_name       工程target名
    --git_url           git 仓库的地址
    --provision_plist   export需要的provisionfile等信息的plist文件
    --branch            git 仓库的分支
    --enviroment        构建的环境，pro/uat/sit
    --build_config      构建的配置选项，比如 Debug，Release
    --info_plist_file   工程的infoplist文件，用于拿版本号等工程信息
    --app_category      app的类别，比如掌上生活是cl, 学生卡是cc
    """

try:
    options, args = getopt.getopt(sys.argv[1:], "h", ["project_root=", "target_name=", "provision_plist=", "enviroment=", "info_plist_file=", "app_category=", "project_file=", "git_url=", "branch=", "build_config="])
except getopt.GetoptError:
    print "不支持的参数类型"
    usage()
    sys.exit()

project_root = None
project_file = None
target_name = None

build_config = None
provision_plist = None

enviroment = None
app_category = None

git_url = None
git_branch = None
info_plist_file = None

for name, value in options:
    if name in ("--project_root"):
        project_root = value
    if name in ("--project_file"):
        project_file = value
    if name in ("--target_name"):
        target_name = value
    if name in ("--build_config"):
        build_config = value
    if name in ("--provision_plist"):
        provision_plist = value
    if name in ("--git_url"):
        git_url = value
    if name in ("--branch"):
        git_branch = value
    if name in ("--enviroment"):
        enviroment = value
    if name in ("--info_plist_file"):
        info_plist_file = value
    if name in ("--app_category"):
        app_category = value
    if name in ("-h"):
        usage()
        sys.exit()

for value in (project_root, project_file, target_name, git_url, provision_plist, git_branch, enviroment, build_config, info_plist_file, app_category):
    if value == None:
        usage()
        sys.exit()

def system(cmd):
    status = os.system(cmd)
    if status != 0:
        exit(1)

def git_co(git_dir, git_branch):
    git_command = "git fetch; git reset --hard; git clean -fd; git checkout " + git_branch + "; git fetch origin " + git_branch + "; git reset --hard origin/" + git_branch
    os.chdir(git_dir)
    system(git_command)

def prepareProject():
    if not os.path.exists(project_root):
        os.makedirs(project_root)
        system("git clone " + git_url + " " + project_root)

    os.chdir(project_root)
    if os.path.isdir("build"):
        shutil.rmtree("build")
    git_co(project_root, git_branch)
    print "===== 工程目录创建成功"

    library_operation = "rm -rf " + project_root + "/library ; ln -s " + project_root + "/../library " + project_root
    os.system(library_operation)
    git_co(project_root + "/library", git_branch)
    print "===== library 目录更新完成"

    modulesLib_operation = "rm -rf " + project_root + "/modulesLib; ln -s " + project_root + "/../modulesLib " + project_root
    os.system(modulesLib_operation)
    git_co(project_root + "/modulesLib", git_branch)
    print "===== modulesLib 目录更新完成"

def build():
    archive_path = project_root + "/build/" + target_name + ".xcarchive"
    archive_command = "xcodebuild -project " + project_file + " -sdk iphoneos -configuration Release clean -scheme " + target_name + " archive -archivePath " + archive_path
    system(archive_command)
    export_command = "xcodebuild -exportArchive -archivePath " + archive_path + " -exportPath " + project_root + "/build/ -exportOptionsPlist " + provision_plist
    system(export_command)

def upload(filePath, category = 'cl'):

    filePath = project_root + '/build/' + target_name + '.ipa'

    register_openers()
    url = 'TODO.json'

    buildTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
    
    infos = biplist.readPlist(info_plist_file)
    outerV_ori = infos['CFBundleShortVersionString']
    outerV = outerV_ori.replace('.', '')
    innerV = '1000'
    codeTime = time.strftime("%Y%m%d%H%M%S")
    buildCode = outerV + innerV + codeTime


    data = { 'buildCode':buildCode, 'os':'2', 'fileName':target_name + '.ipa', 'env':enviroment, 'safe':'0', 'appType':'0', 'branch':git_branch, 'version':outerV_ori, 'buildTime':buildTime, 'appCategory':app_category, 'file':open(filePath) }
    datagen, headers = multipart_encode(data)
    request = urllib2.Request(url, datagen, headers)
    result = urllib2.urlopen(request).read()
    print result

prepareProject()
build()
upload('', '')
