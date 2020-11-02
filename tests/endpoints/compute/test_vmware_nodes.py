# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
from tests.utils import asyncio_patch
from unittest.mock import patch


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def vm(compute_api, compute_project, vmx_path):

    params = {
        "name": "VMTEST",
        "vmx_path": vmx_path,
        "linked_clone": False
    }

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.create", return_value=True) as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes".format(project_id=compute_project.id), params)
    assert mock.called
    assert response.status_code == 201, response.body.decode()
    return response.json


@pytest.fixture
@pytest.mark.asyncio
def vmx_path(tmpdir):
    """
    Return a fake VMX file
    """

    path = str(tmpdir / "test.vmx")
    with open(path, 'w+') as f:
        f.write("1")
    return path


@pytest.mark.asyncio
async def test_vmware_create(compute_api, compute_project, vmx_path):

    params = {
        "name": "VM1",
        "vmx_path": vmx_path,
        "linked_clone": False
    }

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.create", return_value=True):
        response = await compute_api.post("/projects/{project_id}/vmware/nodes".format(project_id=compute_project.id), params)
        assert response.status_code == 201, response.body.decode()
        assert response.json["name"] == "VM1"
        assert response.json["project_id"] == compute_project.id


@pytest.mark.asyncio
async def test_vmware_get(compute_api, compute_project, vm):

    response = await compute_api.get("/projects/{project_id}/vmware/nodes/{node_id}".format(project_id=vm["project_id"], node_id=vm["node_id"]))
    assert response.status_code == 200
    assert response.json["name"] == "VMTEST"
    assert response.json["project_id"] == compute_project.id


@pytest.mark.asyncio
async def test_vmware_start(compute_api, vm):

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.check_hw_virtualization", return_value=True) as mock1:
        with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.start", return_value=True) as mock2:
            response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/start".format(project_id=vm["project_id"], node_id=vm["node_id"]))
            assert mock1.called
            assert mock2.called
            assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_stop(compute_api, vm):

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.stop", return_value=True) as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/stop".format(project_id=vm["project_id"], node_id=vm["node_id"]))
        assert mock.called
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_suspend(compute_api, vm):

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.suspend", return_value=True) as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/suspend".format(project_id=vm["project_id"], node_id=vm["node_id"]))
        assert mock.called
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_resume(compute_api, vm):

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.resume", return_value=True) as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/resume".format(project_id=vm["project_id"], node_id=vm["node_id"]))
        assert mock.called
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_reload(compute_api, vm):

    with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.reload", return_value=True) as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/reload".format(project_id=vm["project_id"], node_id=vm["node_id"]))
        assert mock.called
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_nio_create_udp(compute_api, vm):

    params = {
        "type": "nio_udp",
        "lport": 4242,
        "rport": 4343,
        "rhost": "127.0.0.1"
    }

    with asyncio_patch('gns3server.compute.vmware.vmware_vm.VMwareVM.adapter_add_nio_binding') as mock:
        response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/nio".format(project_id=vm["project_id"], node_id=vm["node_id"]), params)
        assert mock.called
        args, kwgars = mock.call_args
        assert args[0] == 0

    assert response.status_code == 201
    assert response.json["type"] == "nio_udp"


# @pytest.mark.asyncio
# async def test_vmware_nio_update_udp(compute_api, vm):
#
#     params = {
#         "type": "nio_udp",
#         "lport": 4242,
#         "rport": 4343,
#         "rhost": "127.0.0.1",
#         "filters": {}
#     }
#
#     with asyncio_patch('gns3server.compute.vmware.vmware_vm.VMwareVM._ubridge_send'):
#         with asyncio_patch('gns3server.compute.vmware.vmware_vm.VMwareVM.ethernet_adapters'):
#             with patch('gns3server.compute.vmware.vmware_vm.VMwareVM._get_vnet') as mock:
#                 response = await compute_api.put("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/nio".format(project_id=vm["project_id"], node_id=vm["node_id"]), params)
#                 assert response.status_code == 201
#                 assert response.json["type"] == "nio_udp"


@pytest.mark.asyncio
async def test_vmware_delete_nio(compute_api, vm):

    with asyncio_patch('gns3server.compute.vmware.vmware_vm.VMwareVM.adapter_remove_nio_binding') as mock:
        response = await compute_api.delete("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/nio".format(project_id=vm["project_id"], node_id=vm["node_id"]))
        assert mock.called
        args, kwgars = mock.call_args
        assert args[0] == 0

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_vmware_update(compute_api, vm, free_console_port):

    params = {
        "name": "test",
        "console": free_console_port
    }

    response = await compute_api.put("/projects/{project_id}/vmware/nodes/{node_id}".format(project_id=vm["project_id"], node_id=vm["node_id"]), params)
    assert response.status_code == 200
    assert response.json["name"] == "test"
    assert response.json["console"] == free_console_port


@pytest.mark.asyncio
async def test_vmware_start_capture(compute_api, vm):

    params = {
        "capture_file_name": "test.pcap",
        "data_link_type": "DLT_EN10MB"
    }

    with patch("gns3server.compute.vmware.vmware_vm.VMwareVM.is_running", return_value=True):
        with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.start_capture") as mock:

            response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/capture/start".format(project_id=vm["project_id"], node_id=vm["node_id"]), body=params)
            assert response.status_code == 200
            assert mock.called
            assert "test.pcap" in response.json["pcap_file_path"]


@pytest.mark.asyncio
async def test_vmware_stop_capture(compute_api, vm):

    with patch("gns3server.compute.vmware.vmware_vm.VMwareVM.is_running", return_value=True):
        with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.stop_capture") as mock:
            response = await compute_api.post("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/capture/stop".format(project_id=vm["project_id"], node_id=vm["node_id"]))
            assert response.status_code == 204
            assert mock.called


# @pytest.mark.asyncio
# async def test_vmware_pcap(compute_api, vm, compute_project):
#
#     with asyncio_patch("gns3server.compute.vmware.vmware_vm.VMwareVM.get_nio"):
#         with asyncio_patch("gns3server.compute.vmware.VMware.stream_pcap_file"):
#             response = await compute_api.get("/projects/{project_id}/vmware/nodes/{node_id}/adapters/0/ports/0/pcap".format(project_id=compute_project.id, node_id=vm["node_id"]), raw=True)
#             assert response.status_code == 200
