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

"""
API endpoints for Dynamips nodes.
"""

import os
import sys

from fastapi import APIRouter, WebSocket, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from typing import List
from uuid import UUID

from gns3server.compute.dynamips import Dynamips
from gns3server.compute.dynamips.nodes.router import Router
from gns3server.compute.dynamips.dynamips_error import DynamipsError
from gns3server import schemas

router = APIRouter()

responses = {
    404: {"model": schemas.ErrorMessage, "description": "Could not find project or Dynamips node"}
}

DEFAULT_CHASSIS = {
    "c1700": "1720",
    "c2600": "2610",
    "c3600": "3640"
}


def dep_node(project_id: UUID, node_id: UUID):
    """
    Dependency to retrieve a node.
    """

    dynamips_manager = Dynamips.instance()
    node = dynamips_manager.get_node(str(node_id), project_id=str(project_id))
    return node


@router.post("",
             response_model=schemas.Dynamips,
             status_code=status.HTTP_201_CREATED,
             responses={409: {"model": schemas.ErrorMessage, "description": "Could not create Dynamips node"}})
async def create_router(project_id: UUID, node_data: schemas.DynamipsCreate):
    """
    Create a new Dynamips router.
    """

    dynamips_manager = Dynamips.instance()
    platform = node_data.platform
    chassis = None
    if not node_data.chassis and platform in DEFAULT_CHASSIS:
        chassis = DEFAULT_CHASSIS[platform]
    node_data = jsonable_encoder(node_data, exclude_unset=True)
    vm = await dynamips_manager.create_node(node_data.pop("name"),
                                            str(project_id),
                                            node_data.get("node_id"),
                                            dynamips_id=node_data.get("dynamips_id"),
                                            platform=platform,
                                            console=node_data.get("console"),
                                            console_type=node_data.get("console_type", "telnet"),
                                            aux=node_data.get("aux"),
                                            aux_type=node_data.pop("aux_type", "none"),
                                            chassis=chassis,
                                            node_type="dynamips")
    await dynamips_manager.update_vm_settings(vm, node_data)
    return vm.__json__()


@router.get("/{node_id}",
            response_model=schemas.Dynamips,
            responses=responses)
def get_router(node: Router = Depends(dep_node)):
    """
    Return Dynamips router.
    """

    return node.__json__()


@router.put("/{node_id}",
            response_model=schemas.Dynamips,
            responses=responses)
async def update_router(node_data: schemas.DynamipsUpdate, node: Router = Depends(dep_node)):
    """
    Update a Dynamips router.
    """

    await Dynamips.instance().update_vm_settings(node, jsonable_encoder(node_data, exclude_unset=True))
    node.updated()
    return node.__json__()


@router.delete("/{node_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses=responses)
async def delete_router(node: Router = Depends(dep_node)):
    """
    Delete a Dynamips router.
    """

    await Dynamips.instance().delete_node(node.id)


@router.post("/{node_id}/start",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def start_router(node: Router = Depends(dep_node)):
    """
    Start a Dynamips router.
    """

    try:
        await Dynamips.instance().ghost_ios_support(node)
    except GeneratorExit:
        pass
    await node.start()


@router.post("/{node_id}/stop",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def stop_router(node: Router = Depends(dep_node)):
    """
    Stop a Dynamips router.
    """

    await node.stop()


@router.post("/{node_id}/suspend",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def suspend_router(node: Router = Depends(dep_node)):

    await node.suspend()


@router.post("/{node_id}/resume",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def resume_router(node: Router = Depends(dep_node)):
    """
    Resume a suspended Dynamips router.
    """

    await node.resume()


@router.post("/{node_id}/reload",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def reload_router(node: Router = Depends(dep_node)):
    """
    Reload a suspended Dynamips router.
    """

    await node.reload()


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/nio",
             status_code=status.HTTP_201_CREATED,
             response_model=schemas.UDPNIO,
             responses=responses)
async def create_nio(adapter_number: int, port_number: int, nio_data: schemas.UDPNIO, node: Router = Depends(dep_node)):
    """
    Add a NIO (Network Input/Output) to the node.
    """

    nio = await Dynamips.instance().create_nio(node, jsonable_encoder(nio_data, exclude_unset=True))
    await node.slot_add_nio_binding(adapter_number, port_number, nio)
    return nio.__json__()


@router.put("/{node_id}/adapters/{adapter_number}/ports/{port_number}/nio",
            status_code=status.HTTP_201_CREATED,
            response_model=schemas.UDPNIO,
            responses=responses)
async def update_nio(adapter_number: int, port_number: int, nio_data: schemas.UDPNIO, node: Router = Depends(dep_node)):
    """
    Update a NIO (Network Input/Output) on the node.
    """

    nio = node.get_nio(adapter_number, port_number)
    if nio_data.filters:
        nio.filters = nio_data.filters
    await node.slot_update_nio_binding(adapter_number, port_number, nio)
    return nio.__json__()


@router.delete("/{node_id}/adapters/{adapter_number}/ports/{port_number}/nio",
               status_code=status.HTTP_204_NO_CONTENT,
               responses=responses)
async def delete_nio(adapter_number: int, port_number: int, node: Router = Depends(dep_node)):
    """
    Delete a NIO (Network Input/Output) from the node.
    """

    nio = await node.slot_remove_nio_binding(adapter_number, port_number)
    await nio.delete()


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/start_capture",
             responses=responses)
async def start_capture(adapter_number: int,
                        port_number: int,
                        node_capture_data: schemas.NodeCapture,
                        node: Router = Depends(dep_node)):
    """
    Start a packet capture on the node.
    """

    pcap_file_path = os.path.join(node.project.capture_working_directory(), node_capture_data.capture_file_name)

    if sys.platform.startswith('win'):
        # FIXME: Dynamips (Cygwin actually) doesn't like non ascii paths on Windows
        try:
            pcap_file_path.encode('ascii')
        except UnicodeEncodeError:
            raise DynamipsError('The capture file path "{}" must only contain ASCII (English) characters'.format(pcap_file_path))

    await node.start_capture(adapter_number, port_number, pcap_file_path, node_capture_data.data_link_type)
    return {"pcap_file_path": pcap_file_path}


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/stop_capture",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def stop_capture(adapter_number: int, port_number: int, node: Router = Depends(dep_node)):
    """
    Stop a packet capture on the node.
    """

    await node.stop_capture(adapter_number, port_number)


@router.get("/{node_id}/adapters/{adapter_number}/ports/{port_number}/pcap",
            responses=responses)
async def stream_pcap_file(adapter_number: int, port_number: int, node: Router = Depends(dep_node)):
    """
    Stream the pcap capture file.
    """

    nio = node.get_nio(adapter_number, port_number)
    stream = Dynamips.instance().stream_pcap_file(nio, node.project.id)
    return StreamingResponse(stream, media_type="application/vnd.tcpdump.pcap")


@router.get("/{node_id}/idlepc_proposals",
            responses=responses)
async def get_idlepcs(node: Router = Depends(dep_node)) -> List[str]:
    """
    Retrieve Dynamips idle-pc proposals
    """

    await node.set_idlepc("0x0")
    return await node.get_idle_pc_prop()


@router.get("/{node_id}/auto_idlepc",
            responses=responses)
async def get_auto_idlepc(node: Router = Depends(dep_node)) -> dict:
    """
    Get an automatically guessed best idle-pc value.
    """

    idlepc = await Dynamips.instance().auto_idlepc(node)
    return {"idlepc": idlepc}


@router.post("/{node_id}/duplicate",
             status_code=status.HTTP_201_CREATED,
             responses=responses)
async def duplicate_router(destination_node_id: UUID, node: Router = Depends(dep_node)):
    """
    Duplicate a router.
    """

    new_node = await Dynamips.instance().duplicate_node(node.id, str(destination_node_id))
    return new_node.__json__()


@router.websocket("/{node_id}/console/ws")
async def console_ws(websocket: WebSocket, node: Router = Depends(dep_node)):
    """
    Console WebSocket.
    """

    await node.start_websocket_console(websocket)


@router.post("/{node_id}/console/reset",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def reset_console(node: Router = Depends(dep_node)):

    await node.reset_console()