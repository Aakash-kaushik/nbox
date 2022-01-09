# this file has the utilities and functions required for processing Operator items
# to Airlfow specific operations

import inspect # used for __doc__
from functools import partial
from datetime import timedelta

try:
  from airflow.models.baseoperator import BaseOperator
  from airflow.models.dag import DAG
except ImportError:
  pass

from nbox.utils import isthere


def to_airflow_operator(operator, timeout: timedelta = None, operator_kwargs = {}):
  """
  Args:
      operator (Operator): nbox.Operator object to be converted to Airflow Operator
      timeout (timedelta, default=None): in how many seconds the operator should timeout
  """
  operator_kwargs_dict = {}

  # we consider our SLA as the timeout
  # ----------------------------------
  # :param execution_timeout: max time allowed for the execution of
  #      this task instance, if it goes beyond it will raise and fail.
  # :param sla: time by which the job is expected to succeed. Note that
  #      this represents the ``timedelta`` after the period is closed. For
  #      example if you set an SLA of 1 hour, the scheduler would send an email
  #      soon after 1:00AM on the ``2016-01-02`` if the ``2016-01-01`` instance
  #      has not succeeded yet.
  #      The scheduler pays special attention for jobs with an SLA and
  #      sends alert
  #      emails for SLA misses. SLA misses are also recorded in the database
  #      for future reference. All tasks that share the same SLA time
  #      get bundled in a single email, sent soon after that time. SLA
  #      notification are sent once and only once for each task instance.
  operator_kwargs_dict["execution_timeout"] = timeout
  operator_kwargs_dict["sla"] = timeout
  operator_kwargs_dict["task_id"] = operator.__class__.__name__

  try:
    comms = operator.comms()
  except:
    comms = {}

  # this is currently assumed to be rst text because this is what we are using
  # for documentation at NBX
  doc = operator.__doc__ # this is in between class xxx and def __init__
  doc = doc if doc else ""
  init_doc = inspect.getdoc(operator.__init__) # this is doc for __init__
  init_doc = init_doc if init_doc else ""
  full_doc = doc + "\n" + init_doc
  full_doc = None if not full_doc else full_doc
  operator_kwargs_dict["doc_rst"] = full_doc

  # update the dict with information
  operator_kwargs_dict.update(comms)
  operator_kwargs_dict.update(operator_kwargs)

  operator = BaseOperator(
    # items planned to be supported
    email = None,
    email_on_retry = False,
    email_on_failure = False,
    
    # documentation to be handled, currently assumed to be rst documentation
    doc = None,
    doc_md = None,
    doc_json = None,
    doc_yaml = None,

    # these can be the hooks that user defines for Operators
    # ie. is the airflow.operator executes user defines which of
    # their functions to call
    on_execute_callback = None,
    on_failure_callback = None,
    on_success_callback = None,
    on_retry_callback = None,

    # others are ignored as of now

    **operator_kwargs_dict
  )

  return operator

def from_airflow_operator(operator_cls, air_operator):
  assert air_operator.__class__.__name__ != "PythonOperator", \
    "Only PythonOperator is supported at the moment"
  op = operator_cls()
  op._register_forward(air_operator.python_callable)
  return op

def to_airflow_dag(operator, dag, operator_kwrags, dag_kwargs):
  operator = to_airflow_operator(operator, **operator_kwrags)
  dag = DAG(
    dag_id = "DAG_" + operator.task_id,
    **dag_kwargs
  )
  return dag

def from_airflow_dag(operator_cls, dag):
  task_group = dag.task_group # the DAG structure is inside dag.task_group

  topo_tree = {}
  for x in task_group:
    if x.__class__.__name__ != "PythonOperator":
      raise Exception("Only PythonOperator is supported at the moment")
    topo_tree[x.task_id] = [_x.task_id for _x in x.get_direct_relatives(upstream = True)]

  # from this topo tree create nbox operator for this dag
  root = operator_cls()
  all_ops = {}
  parent_less_ops = []
  for child, parents in topo_tree.items():
    if child not in all_ops:
      all_ops[child] = operator_cls()
      all_ops[child]._register_forward(dag.task_dict[child].python_callable)
    for p in parents:
      if p not in all_ops:
        all_ops[p] = operator_cls()
      setattr(
        all_ops[p], f"op__{p}__{child}", all_ops[child]
      )
      try:
        all_ops[p]._register_forward(dag.task_dict[p].python_callable)
      except:
        pass

    if not parents:
      parent_less_ops.append(child)

  for p in parent_less_ops:
    name = f"op__root__{p}"
    setattr(root, name, all_ops[p])

  def sequential_forward(ops, **kwargs):
    out = kwargs
    for o in ops:
      out = o(**out)
      if not out:
        out = {}
    return out

  forward = partial(sequential_forward, ops = root.operators())
  root._register_forward(forward)

  return root


class AirflowMixin:
  @isthere("airflow")
  def to_airflow_operator(self, timeout, **operator_kwargs):
    return to_airflow_operator(self, timeout, operator_kwargs)

  @classmethod
  @isthere("airflow")
  def from_airflow_operator(cls, air_operator):
    return from_airflow_operator(cls, air_operator)

  @isthere("airflow")
  def to_airflow_dag(self, dag_kwargs, operator_kwargs):
    return to_airflow_dag(self, dag_kwargs, operator_kwargs)

  @classmethod
  @isthere("airflow")
  def from_airflow_dag(cls, dag):
    return from_airflow_dag(cls, dag)


__all__ = ["AirflowMixin"]