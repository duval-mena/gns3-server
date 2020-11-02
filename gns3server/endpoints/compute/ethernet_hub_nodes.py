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
API endpoints for Ethernet hub nodes.
"""

import os

from fastapi import APIRouter, Depends, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from uuid import UUID

from gns3server.compute.dynamips import Dynamips
from gns3server.compute.dynamips.nodes.ethernet_hub import EthernetHub
from gns3server import schemas

router = APIRouter()

responses = {
    404: {"model": schemas.ErrorMessage, "description": "Could not find project or Ethernet hub node"}
}


def dep_node(project_id: UUID, node_id: UUID):
    """
    Dependency to retrieve a node.
    """

    dynamips_manager = Dynamips.instance()
    node = dynamips_manager.get_node(str(node_id), project_id=str(project_id))
    return node


@router.post("",
             response_model=schemas.EthernetHub,
             status_code=status.HTTP_201_CREATED,
             responses={409: {"model": schemas.ErrorMessage, "description": "Could not create Ethernet hub node"}})
async def create_ethernet_hub(project_id: UUID, node_data: schemas.EthernetHubCreate):
    """
    Create a new Ethernet hub.
    """

    # Use the Dynamips Ethernet hub to simulate this node
    dynamips_manager = Dynamips.instance()
    node_data = jsonable_encoder(node_data, exclude_unset=True)
    node = await dynamips_manager.create_node(node_data.pop("name"),
                                              str(project_id),
                                              node_data.get("node_id"),
                                              node_type="ethernet_hub",
                                              ports=node_data.get("ports_mapping"))
    return node.__json__()


@router.get("/{node_id}",
            response_model=schemas.EthernetHub,
            responses=responses)
def get_ethernet_hub(node: EthernetHub = Depends(dep_node)):
    """
    Return an Ethernet hub.
    """

    return node.__json__()


@router.post("/{node_id}/duplicate",
             response_model=schemas.EthernetHub,
             status_code=status.HTTP_201_CREATED,
             responses=responses)
async def duplicate_ethernet_hub(destination_node_id: UUID = Body(..., embed=True),
                                 node: EthernetHub = Depends(dep_node)):
    """
    Duplicate an Ethernet hub.
    """

    new_node = await Dynamips.instance().duplicate_node(node.id, str(destination_node_id))
    return new_node.__json__()


@router.put("/{node_id}",
            response_model=schemas.EthernetHub,
            responses=responses)
async def update_ethernet_hub(node_data: schemas.EthernetHubUpdate, node: EthernetHub = Depends(dep_node)):
    """
    Update an Ethernet hub.
    """

    node_data = jsonable_encoder(node_data, exclude_unset=True)
    if "name" in node_data and node.name != node_data["name"]:
        await node.set_name(node_data["name"])
    if "ports_mapping" in node_data:
        node.ports_mapping = node_data["ports_mapping"]
    node.updated()
    return node.__json__()


@router.delete("/{node_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses=responses)
async def delete_ethernet_hub(node: EthernetHub = Depends(dep_node)):
    """
    Delete an Ethernet hub.
    """

    await Dynamips.instance().delete_node(node.id)


@router.post("/{node_id}/start",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
def start_ethernet_hub(node: EthernetHub = Depends(dep_node)):
    """
    Start an Ethernet hub.
    This endpoint results in no action since Ethernet hub nodes are always on.
    """

    pass


@router.post("/{node_id}/stop",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
def stop_ethernet_hub(node: EthernetHub = Depends(dep_node)):
    """
    Stop an Ethernet hub.
    This endpoint results in no action since Ethernet hub nodes are always on.
    """

    pass


@router.post("/{node_id}/suspend",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
def suspend_ethernet_hub(node: EthernetHub = Depends(dep_node)):
    """
    Suspend an Ethernet hub.
    This endpoint results in no action since Ethernet hub nodes are always on.
    """

    pass


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/nio",
             status_code=status.HTTP_201_CREATED,
             response_model=schemas.UDPNIO,
             responses=responses)
async def create_nio(adapter_number: int,
                     port_number: int,
                     nio_data: schemas.UDPNIO,
                     node: EthernetHub = Depends(dep_node)):
    """
    Add a NIO (Network Input/Output) to the node.
    The adapter number on the hub is always 0.
    """

    nio = await Dynamips.instance().create_nio(node, jsonable_encoder(nio_data, exclude_unset=True))
    await node.add_nio(nio, port_number)
    return nio.__json__()


@router.delete("/{node_id}/adapters/{adapter_number}/ports/{port_number}/nio",
               status_code=status.HTTP_204_NO_CONTENT,
               responses=responses)
async def delete_nio(adapter_number: int, port_number: int, node: EthernetHub = Depends(dep_node)):
    """
    Delete a NIO (Network Input/Output) from the node.
    The adapter number on the hub is always 0.
    """

    nio = await node.remove_nio(port_number)
    await nio.delete()


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/capture/start",
             responses=responses)
async def start_capture(adapter_number: int,
                        port_number: int,
                        node_capture_data: schemas.NodeCapture,
                        node: EthernetHub = Depends(dep_node)):
    """
    Start a packet capture on the node.
    The adapter number on the hub is always 0.
    """

    pcap_file_path = os.path.join(node.project.capture_working_directory(), node_capture_data.capture_file_name)
    await node.start_capture(port_number, pcap_file_path, node_capture_data.data_link_type)
    return {"pcap_file_path": pcap_file_path}


@router.post("/{node_id}/adapters/{adapter_number}/ports/{port_number}/capture/stop",
             status_code=status.HTTP_204_NO_CONTENT,
             responses=responses)
async def stop_capture(adapter_number: int, port_number: int, node: EthernetHub = Depends(dep_node)):
    """
    Stop a packet capture on the node.
    The adapter number on the hub is always 0.
    """

    await node.stop_capture(port_number)


@router.get("/{node_id}/adapters/{adapter_number}/ports/{port_number}/capture/stream",
            responses=responses)
async def stream_pcap_file(adapter_number: int, port_number: int, node: EthernetHub = Depends(dep_node)):
    """
    Stream the pcap capture file.
    The adapter number on the hub is always 0.
    """

    nio = node.get_nio(port_number)
    stream = Dynamips.instance().stream_pcap_file(nio, node.project.id)
    return StreamingResponse(stream, media_type="application/vnd.tcpdump.pcap")
