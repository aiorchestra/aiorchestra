#    Author: Denys Makogon
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import asyncio


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


async def retry(fn, args=None, kwargs=None, exceptions=None,
                task_retries=1, task_retry_interval=10):
    """
    Retry operation coroutine-handler for operation that
    are requiring polling for object changes.

    :param fn: retry coroutine
    :param args: retry coroutine args
    :param kwargs: retry coroutine kwargs
    :param exceptions: exception that are meant to be as not critical
                       and would not stop retrying
    :param task_retries: number of retries for retry coroutine
    :param task_retry_interval: retry interval for retry
                                coroutine between retries
    :return: result
    :rtype: object
    """
    args = args or []
    kwargs = kwargs or {}

    while task_retries > 0:
        try:
            result = await fn(*args, **kwargs)
            if result:
                return result
        except Exception as e:
            if not exceptions or not isinstance(e, exceptions):
                raise e
        if task_retry_interval:
            await asyncio.sleep(task_retry_interval)
        task_retries -= 1
    raise Exception("exiting retry loop")


def operation(action):
    """
    Node lifecycle event operation coroutine-handler

    :param action: node lifecycle event
    :type action: awaitable
    :return: None
    :rtype: None
    """
    async def wraps(*args, **kwargs):
        source = list(args)[0]
        source.context.logger.debug(
            '[{0}] - staring task "{1}" execution.'
            .format(source.name, action.__name__))
        try:
            await action(*args, **kwargs)
            source.context.logger.debug(
                '[{0}] - ending task "{1}" execution'
                .format(source.name, action.__name__))
        except Exception as ex:
            source.context.logger.error(
                '[{0}] - error during task "{1}" execution. '
                'Reason: {2}.'
                .format(source.name, action.__name__, str(ex)))
            if not source.context.rollback_enabled:
                raise ex
    return wraps
