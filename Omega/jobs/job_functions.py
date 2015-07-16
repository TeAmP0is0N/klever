from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from jobs.job_model import JOB_ROLES
from users.models import USER_ROLES
from reports.models import STATUS


COLORS = {
    'red': '#C70646',
    'orange': '#D05A00',
    'purple': '#930BBD',
}

# List of available types of 'safe' column class.
SAFES = [
    'missed_bug',
    'incorrect',
    'unknown',
    'inconclusive',
    'unassociated',
    'total'
]

# List of available types of 'unsafe' column class.
UNSAFES = [
    'bug',
    'target_bug',
    'false_positive',
    'unknown',
    'inconclusive',
    'unassociated',
    'total'
]

# Dictionary of titles of static columns
TITLES = {
    'name': _('Title'),
    'author': _('Author'),
    'date': _('Date'),
    'status': _('Status'),
    'safe': _('Safes'),
    'safe:missed_bug': _('Missed bug'),
    'safe:incorrect': _('Incorrect proof'),
    'safe:unknown': _('Unknown'),
    'safe:inconclusive': _('Inconclusive'),
    'safe:unassociated': _('Unassociated'),
    'safe:total': _('Total'),
    'unsafe': _('Unsafes'),
    'unsafe:bug': _('Bug'),
    'unsafe:target_bug': _('Target bug'),
    'unsafe:false_positive': _('False positive'),
    'unsafe:unknown': _('Unknown'),
    'unsafe:inconclusive': _('Inconclusive'),
    'unsafe:unassociated': _('Unassociated'),
    'unsafe:total': _('Total'),
    'problem': _('Unknowns'),
    'problem:total': _('Total'),
    'resource': _('Resourses'),
    'resource:total': _('Total'),
    'tag': _('Tags'),
    'tag:safe': _('Safe tags'),
    'tag:unsafe': _('Unsafe tags'),
    'identifier': _('Identifier'),
    'format': _('Format'),
    'version': _('Version'),
    'type': _('Job type'),
    'parent_name': _('Parent name'),
    'parent_id': _('Parent identifier'),
    'role': _('Your role'),
}


def convert_time(val, acc):
    new_time = int(val)
    time_format = "%%1.%df%%s" % int(acc)
    try_div = new_time / 1000
    if try_div < 1:
        return time_format % (new_time, 'ms')
    new_time = try_div
    try_div = new_time / 60
    if try_div < 1:
        return time_format % (new_time, 's')
    new_time = try_div
    try_div = new_time / 60
    if try_div < 1:
        return time_format % (new_time, 'm')
    return time_format % (try_div, 'h')


def convert_memory(val, acc):
    new_mem = int(val)
    mem_format = "%%1.%df%%s" % int(acc)
    try_div = new_mem / 1024
    if try_div < 1:
        return mem_format % (new_mem, 'b')
    new_mem = try_div
    try_div = new_mem / 1024
    if try_div < 1:
        return mem_format % (new_mem, 'Kb')
    new_mem = try_div
    try_div = new_mem / 1024
    if try_div < 1:
        return mem_format % (new_mem, 'Mb')
    return mem_format % (try_div, 'Gb')


def verdict_info(job):
    try:
        verdicts = job.verdict
    except ObjectDoesNotExist:
        return None

    safes_data = []
    for s in SAFES:
        safe_name = 'safe:' + s
        color = None
        val = '-'
        if s == 'missed_bug':
            val = verdicts.safe_missed_bug
            color = COLORS['red']
        elif s == 'incorrect':
            val = verdicts.safe_incorrect_proof
            color = COLORS['orange']
        elif s == 'unknown':
            val = verdicts.safe_unknown
            color = COLORS['purple']
        elif s == 'inconclusive':
            val = verdicts.safe_inconclusive
            color = COLORS['red']
        elif s == 'unassociated':
            val = verdicts.safe_unassociated
        elif s == 'total':
            val = verdicts.safe
        safes_data.append({
            'title': TITLES[safe_name],
            'value': val,
            'color': color,
        })

    unsafes_data = []
    for s in UNSAFES:
        unsafe_name = 'unsafe:' + s
        color = None
        val = '-'
        if s == 'bug':
            val = verdicts.unsafe_bug
            color = COLORS['red']
        elif s == 'target_bug':
            val = verdicts.unsafe_target_bug
            color = COLORS['red']
        elif s == 'false_positive':
            val = verdicts.unsafe_false_positive
            color = COLORS['orange']
        elif s == 'unknown':
            val = verdicts.unsafe_unknown
            color = COLORS['purple']
        elif s == 'inconclusive':
            val = verdicts.unsafe_inconclusive
            color = COLORS['red']
        elif s == 'unassociated':
            val = verdicts.unsafe_unassociated
        elif s == 'total':
            val = verdicts.unsafe
        unsafes_data.append({
            'title': TITLES[unsafe_name],
            'value': val,
            'color': color,
        })
    return {
        'unsafes': unsafes_data,
        'safes': safes_data,
        'unknowns': verdicts.unknown
    }


def unknowns_info(job):
    unknowns_data = {}
    unkn_set = job.componentmarkunknownproblem_set.filter(~Q(problem=None))
    for cmup in unkn_set:
        if cmup.component.name not in unknowns_data:
            unknowns_data[cmup.component.name] = {}
        unknowns_data[cmup.component.name][cmup.problem.name] = cmup.number
    unkn_set = job.componentmarkunknownproblem_set.filter(problem=None)
    for cmup in unkn_set:
        if cmup.component.name not in unknowns_data:
            unknowns_data[cmup.component.name] = {}
        unknowns_data[cmup.component.name][_('No mark')] = cmup.number
    unkn_set = job.componentunknown_set.all()
    for cmup in unkn_set:
        if cmup.component.name not in unknowns_data:
            unknowns_data[cmup.component.name] = {}
        unknowns_data[cmup.component.name][_('Total')] = cmup.number
    unknowns_sorted = []
    for comp in sorted(unknowns_data):
        problems_sorted = []
        for probl in unknowns_data[comp]:
            problems_sorted.append({
                'num': unknowns_data[comp][probl],
                'problem': probl,
            })
        unknowns_sorted.append({
            'component': comp,
            'problems': problems_sorted,
        })
    return unknowns_sorted


def resource_info(job, user):
    accuracy = user.extended.accuracy
    data_format = user.extended.data_format

    res_set = job.componentresource_set.filter(~Q(component=None))
    res_data = {}
    for cr in res_set:
        if cr.component.name not in res_data:
            res_data[cr.component.name] = {}
        wall = cr.wall_time
        cpu = cr.cpu_time
        mem = cr.memory
        if data_format == 'hum':
            wall = convert_time(wall, accuracy)
            cpu = convert_time(cpu, accuracy)
            mem = convert_memory(mem, accuracy)
        res_data[cr.component.name] = "%s %s %s" % (wall, cpu, mem)
    resource_data = [
        {'component': x, 'val': res_data[x]} for x in sorted(res_data)]
    res_total = job.componentresource_set.filter(component=None)
    if len(res_total):
        wall = res_total[0].wall_time
        cpu = res_total[0].cpu_time
        mem = res_total[0].memory
        if data_format == 'hum':
            wall = convert_time(wall, accuracy)
            cpu = convert_time(cpu, accuracy)
            mem = convert_memory(mem, accuracy)
        total_value = "%s %s %s" % (wall, cpu, mem)
        resource_data.append({
            'component': _('Total'),
            'val': total_value,
        })
    return resource_data


def role_info(job, user):
    roles_data = {'global': job.global_role}

    users = []
    user_roles_data = []
    users_roles = job.userrole_set.filter(~Q(user=user))
    for ur in users_roles:
        title = ur.user.extended.last_name + ' ' + ur.user.extended.first_name
        u_id = ur.user_id
        user_roles_data.append({
            'user': {'id': u_id, 'name': title},
            'role': {'val': ur.role, 'title': ur.get_role_display()}
        })
        users.append(u_id)

    roles_data['user_roles'] = user_roles_data

    available_users = []
    for u in User.objects.filter(~Q(pk__in=users) & ~Q(pk=user.pk)):
        available_users.append({
            'id': u.pk,
            'name': u.extended.last_name + ' ' + u.extended.first_name
        })
    roles_data['available_users'] = available_users

    available_roles = []
    for role in JOB_ROLES:
        available_roles.append({
            'value': role[0],
            'title': role[1],
        })
    roles_data['job_roles'] = available_roles
    return roles_data


def has_job_access(user, action='view', job=None):
    if action == 'view' and job:
        if user.extended.role == USER_ROLES[2][0]:
            return True
        job_first_ver = job.jobhistory_set.filter(version=1)
        if len(job_first_ver) and job_first_ver[0].change_author == user:
            return True
        user_role = job.userrole_set.filter(user=user)
        if len(user_role):
            if user_role[0].role == JOB_ROLES[0][0]:
                return False
            return True
        if job.global_role == JOB_ROLES[0][0]:
            return False
        return True
    elif action == 'create':
        return user.extended.role == USER_ROLES[1][0]
    elif action == 'edit' and job:
        first_v = job.jobhistory_set.filter(version=1)
        if first_v:
            try:
                status = job.reportroot.status
            except ObjectDoesNotExist:
                # TODO: return False for jobs without status
                return True
            if status == STATUS[0][0]:
                if first_v[0].change_author == user or \
                                user.extended.role == USER_ROLES[2][0]:
                    return True
        return False
    elif action == 'remove' and job:
        if user.extended.role == USER_ROLES[2][0]:
            return True
        first_version = job.jobhistory_set.filter(version=1)
        if len(first_version) and len(job.children_set.all()) == 0:
            try:
                status = job.reportroot.status
            except ObjectDoesNotExist:
                status = None
            if status in [STATUS[1][0], STATUS[2][0], STATUS[3][0]]:
                return False
            if first_version[0].change_author == user:
                return True
    return False
