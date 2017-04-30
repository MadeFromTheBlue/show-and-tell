#! /usr/bin/env python3

"""
Sumbit Project Controller
"""

from bottle import route, get, post, request, redirect, static_file, abort
from showandtell import db, kajiki_view, helpers, model, security_check
import validators
import os

def can_edit(ident, team):
    admin_edit = ident.is_admin and helpers.util.from_config_yaml('admin_edit')
    return (ident and ident in team.members) or admin_edit

# Go to the submit a project page
@route('/projects/<id>/edit')
@route('/submit')
@kajiki_view('edit_project')
def new_project(id=None):
    
    user = model.Session.get_identity()

    # This is slated to be removed for a more complex redirect
    if user == None:
        redirect('/login')

    if id == None:
        project = model.Project(None, None, None, None)
    else:
        project = db.session.query(model.Project).filter_by(project_id=id).one()

    return {
        # Yes, this is a hack to get the text area to work properly
        'empty': '',
        'project': project,
        'teams': user.teams,
        # This is a placeholder for the moment, 
        # I dunno what we're actually doing
        'types': ['Image', 'Video', 'Shell Script'],
        'page': 'submit_project',
    }

# Get the contents submitted from submit a project
@post('/submit/new')
def submit_project():
    user = model.Session.get_identity()

    project_id = request.forms.get('project_id')
    team_id = request.forms.get('team-id')
    # Take the team id and get the team object
    team = db.session.query(model.Team).filter_by(team_id=team_id).one()

    name = request.forms.get('name')
    description = request.forms.get('description')
    project_type = request.forms.get('project-type')
     
    # If the user didn't enter a website, 
    # set it to none so it's null
    website = request.forms.get('website')
    if website == '':
        website = None

    repository = request.forms.get('repository')
    if repository == '':
        repository = None

    project_files = request.files.getall('project-files')        

    # Update all of the text entries for the project
    if not project_id:
        # Create a new row in the project table
        project = model.Project(team, name, description, project_type, website)
    else:
        project = db.session.query(model.Project).filter_by(project_id=project_id).one()
        project.team = team
        project.name = name
        project.description = description
        project.type = project_type
        project.website = website
        project.status = 'unverified'
   
    project.repository = repository

    # Remove any selected files from the project
    num_assets = request.forms.get('num_assets')
    if num_assets:
        for i in range(int(num_assets)):
            cur_asset = request.forms.get('asset-' + str(i))
            
            # Get the assets the user selected and delete them
            if cur_asset:
                # Convert the string into the asset id
                cur_asset = int(cur_asset.split()[-1])

                asset = db.session.query(model.association_tables.ProjectAsset).filter_by(asset_id=cur_asset).one()
                helpers.util.delete_asset(asset.assets.filename)
                project.assets.remove(asset)
            
    # Add any new files that were uploaded to the project
    if project_files:
        for i, file in enumerate(project_files):
            if file.filename and file.file:
                file_path = helpers.util.save_asset(file)

                # Make the cross-reference between the new asset and the project
                xref = model.association_tables.ProjectAsset()
                xref.assets = model.Asset(file.filename, file.filename.split('.')[1], file_path)
                xref.role = "This is currently defunct"
                project.assets.append(xref)
                
    db.session.add(project)
    db.session.commit()
    
    redirect('/projects/' + str(project.project_id))

@route('/projects/<id>')
@kajiki_view('view_project')
def view_project(id):
    
    user = model.Session.get_identity()
    project = db.session.query(model.Project).filter_by(project_id=id).first()

    if not project:
        abort(404, 'Project not found!')

    return {
        'project': project,
        'can_edit': can_edit(user, project.team),
    }

from zipfile import ZipFile

@get('/projects/<id>/download')
def download_project(id):

    project = db.session.query(model.Project).filter_by(project_id=id).first()
    root_path = helpers.util.get_asset_folder()

    if not project.assets:
        return None
    if len(project.assets) == 1:
        asset = project.assets[0].assets
        return static_file(asset.filename, root=root_path, download=asset.name)
    # Yes, this is very ugly
    # I'm very sorry
    else:
        download_name = project.name + '.zip'
        archive_name = 'project_assets.zip'
        archive_path = os.path.join(root_path, archive_name)

        # Get rid of the last archive that was created if it exists
        if os.path.isfile(archive_path):
            os.remove(archive_path)

        archive = ZipFile(archive_path, mode='x')

        # Stick all of the assets into the zip
        for project_asset in project.assets:
            asset = project_asset.assets
            asset_path = os.path.join(root_path, asset.filename)
            archive.write(asset_path, asset.name)

        archive.close()

        return static_file(archive_name, root=root_path, download=download_name)
