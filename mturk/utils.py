import logging
import contextlib
import json
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import List, Dict, Union, Optional

import boto3
from django.conf import settings
from django.contrib import messages
from hr.models import Profile

logger = logging.getLogger(__name__)


@dataclass
class MTurkSettings:
    keywords: Union[str, list]
    title: str
    description: str
    frame_height: int
    template: str
    minutes_allotted_per_assignment: int
    expiration_hours: float
    qualification_requirements: List
    grant_qualification_id: Optional[str] = None


def get_mturk_client(profile: Profile, *, use_sandbox=True):
    if use_sandbox:
        endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    else:
        endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
    return boto3.client(
        'mturk',
        aws_access_key_id=profile.aws_access_key_id,
        aws_secret_access_key=profile.aws_secret_access_key,
        endpoint_url=endpoint_url,
        # if I specify endpoint_url without region_name, it complains
        region_name='us-east-1',
    )


@contextlib.contextmanager
def MTurkClient(profile, *, use_sandbox=True, request):
    '''Alternative to get_mturk_client, for when we need exception handling
    in admin views, we should pass it, so that we can show the user the message
    without crashing.
    for participant-facing views and commandline tools, should use get_mturk_client.
    '''
    try:
        yield get_mturk_client(profile, use_sandbox=use_sandbox)
    except Exception as exc:
        # TODO: instead of catching Exception, we should catch just boto3 errors,
        # and remove the 'raise'
        logger.error('MTurk error', exc_info=True)
        messages.error(request, str(exc), extra_tags='safe')
        raise


AssignmentData = namedtuple(
    'Assignment', ['worker_id', 'assignment_id', 'status', 'answer']
)


def get_all_assignments(mturk_client, hit_ids) -> List[AssignmentData]:
    # Accumulate all relevant assignments, one page of results at
    # a time.
    assignments = []

    for hit_id in hit_ids:
        args = dict(
            HITId=hit_id,
            # i think 100 is the max page size
            MaxResults=100,
            AssignmentStatuses=['Submitted', 'Approved', 'Rejected'],
        )

        while True:
            response = mturk_client.list_assignments_for_hit(**args)
            if not response['Assignments']:
                break
            for d in response['Assignments']:
                assignments.append(
                    AssignmentData(
                        worker_id=d['WorkerId'],
                        assignment_id=d['AssignmentId'],
                        status=d['AssignmentStatus'],
                        answer=d['Answer'],
                    )
                )
            args['NextToken'] = response['NextToken']

    return assignments


def get_worker_ids_by_status(
    all_assignments: List[AssignmentData],
) -> Dict[str, List[str]]:
    workers_by_status = defaultdict(list)
    for assignment in all_assignments:
        workers_by_status[assignment.status].append(assignment.worker_id)
    return workers_by_status


def get_completion_code(xml: str) -> str:
    if not xml:
        return ''
    # move inside function because it adds 0.03s to startup time
    from xml.etree import ElementTree

    root = ElementTree.fromstring(xml)
    for ans in root:
        if ans[0].text == 'taskAnswers':
            answer_data = json.loads(ans[1].text)
            try:
                return answer_data[0]['completion_code']
            except:
                return ''
    return ''


def in_public_domain(request):
    """This method validates if oTree are published on a public domain
    because mturk need it

    """
    host = request.get_host().lower()
    if ":" in host:
        host = host.split(":", 1)[0]
    if host in ["localhost", '127.0.0.1']:
        return False
    # IPy had a compat problem with py 3.8.
    # in the future, could move some IPy code here.
    return True
