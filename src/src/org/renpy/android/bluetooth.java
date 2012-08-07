/*
 * Copyright (C) 2010 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

/*
 * forked from android-scripting project
 * http://code.google.com/p/android-scripting/source/browse/android/BluetoothFacade/src/com/googlecode/android_scripting/facade/BluetoothFacade.java
 */

package org.renpy.android;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;

import org.apache.commons.codec.binary.Base64Codec;

/**
 * Bluetooth functions.
 * 
 */
// Discovery functions added by Eden Sayag

public class Bluetooth {

  private Map<String, BluetoothConnection> connections = new HashMap<String, BluetoothConnection>();
  private AndroidFacade mAndroidFacade;
  private BluetoothAdapter mBluetoothAdapter;

  //public BluetoothFacade(FacadeManager manager) {
    //super(manager);
    //mAndroidFacade = manager.getReceiver(AndroidFacade.class);
    //mBluetoothAdapter = MainThread.run(manager.getService(), new Callable<BluetoothAdapter>() {
      //@Override
      //public BluetoothAdapter call() throws Exception {
        //return BluetoothAdapter.getDefaultAdapter();
      //}
    //});
  //}

  public Map<String, String> activeConnections() {
    Map<String, String> out = new HashMap<String, String>();
    for (Map.Entry<String, BluetoothConnection> entry : connections.entrySet()) {
      if (entry.getValue().isConnected()) {
        out.put(entry.getKey(), entry.getValue().getRemoteBluetoothAddress());
      }
    }

    return out;
  }

  private BluetoothConnection getConnection(String connID) throws IOException {
    BluetoothConnection conn = null;
    if (connID.trim().length() > 0) {
      conn = connections.get(connID);
    } else if (connections.size() == 1) {
      conn = (BluetoothConnection) connections.values().toArray()[0];
    }
    if (conn == null) {
      throw new IOException("Bluetooth not ready for this connID.");
    }
    return conn;
  }

  public void writeBinary(String base64, String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      conn.write(Base64Codec.decodeBase64(base64));
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  public String readBinary(Integer bufferSize, String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      return Base64Codec.encodeBase64String(conn.readBinary(bufferSize));
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  private String addConnection(BluetoothConnection conn) {
    String uuid = UUID.randomUUID().toString();
    connections.put(uuid, conn);
    conn.setUUID(uuid);
    return uuid;
  }

  public String connect(String uuid, String address) throws IOException {
    //if (address == null) {
      //Intent deviceChooserIntent = new Intent();
      //deviceChooserIntent.setComponent(Constants.BLUETOOTH_DEVICE_LIST_COMPONENT_NAME);
      //Intent result = mAndroidFacade.startActivityForResult(deviceChooserIntent);
      //if (result != null && result.hasExtra(Constants.EXTRA_DEVICE_ADDRESS)) {
        //address = result.getStringExtra(Constants.EXTRA_DEVICE_ADDRESS);
      //} else {
        //return null;
      //}
    //}
    BluetoothDevice mDevice;
    BluetoothSocket mSocket;
    BluetoothConnection conn;
    mDevice = mBluetoothAdapter.getRemoteDevice(address);
    mSocket = mDevice.createRfcommSocketToServiceRecord(UUID.fromString(uuid));
    // Always cancel discovery because it will slow down a connection.
    mBluetoothAdapter.cancelDiscovery();
    mSocket.connect();
    conn = new BluetoothConnection(mSocket);
    return addConnection(conn);
  }

  public String accept(String uuid, Integer timeout) throws IOException {
    BluetoothServerSocket mServerSocket;
    mServerSocket = mBluetoothAdapter.listenUsingRfcommWithServiceRecord(SDP_NAME, UUID.fromString(uuid));
    BluetoothSocket mSocket = mServerSocket.accept(timeout.intValue());
    BluetoothConnection conn = new BluetoothConnection(mSocket, mServerSocket);
    return addConnection(conn);
  }

  public void makeDiscoverable(Integer duration) {
    if (mBluetoothAdapter.getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE) {
      Intent discoverableIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);
      discoverableIntent.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, duration);
      // Use startActivityForResult to make this a synchronous call.
      mAndroidFacade.startActivityForResult(discoverableIntent);
    }
  }

  public void write(String ascii, String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      conn.write(ascii);
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  public Boolean readReady(String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      return conn.readReady();
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  public String read(Integer bufferSize, String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      return conn.read(bufferSize);
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  public String readLine(String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    try {
      return conn.readLine();
    } catch (IOException e) {
      connections.remove(conn.getUUID());
      throw e;
    }
  }

  public String getRemoteDeviceName(String address) {
    try {
      BluetoothDevice mDevice;
      mDevice = mBluetoothAdapter.getRemoteDevice(address);
      return mDevice.getName();
    } catch (Exception e) {
      return null;
    }
  }

  public String getLocalName() {
    return mBluetoothAdapter.getName();
  }

  public boolean setLocalName(String name) {
    return mBluetoothAdapter.setName(name);
  }

  public String getScanMode() {
    if (mBluetoothAdapter.getState() == BluetoothAdapter.STATE_OFF
        || mBluetoothAdapter.getState() == BluetoothAdapter.STATE_TURNING_OFF) {
      return "disabled";
    }

    switch (mBluetoothAdapter.getScanMode()) {
    case BluetoothAdapter.SCAN_MODE_NONE:
      return "non connectable";
    case BluetoothAdapter.SCAN_MODE_CONNECTABLE:
      return "non discoverable";
    case BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE:
      return "discoverable";
    default:
      return "unknown";
      //return mBluetoothAdapter.getScanMode() - 20;
    }
  }

  public String getConnectedDeviceName(String connID) throws IOException {
    BluetoothConnection conn = getConnection(connID);
    return conn.getConnectedDeviceName();
  }

  public Boolean enabled() {
    return mBluetoothAdapter.isEnabled();
  }

  public Boolean toggle(Boolean enabled, Boolean prompt) {
    if (enabled == null) {
      enabled = !checkBluetoothState();
    }
    if (enabled) {
      if (prompt) {
        Intent intent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
        // TODO(damonkohler): Use the result to determine if this was successful. At any rate, keep
        // using startActivityForResult in order to synchronize this call.
        mAndroidFacade.startActivityForResult(intent);
      } else {
        // TODO(damonkohler): Make this synchronous as well.
        mBluetoothAdapter.enable();
      }
    } else {
      // TODO(damonkohler): Add support for prompting on disable.
      // TODO(damonkohler): Make this synchronous as well.
      shutdown();
      mBluetoothAdapter.disable();
    }
    return enabled;
  }

  public void bluetoothStop(String connID) {
    BluetoothConnection conn;
    try {
      conn = getConnection(connID);
    } catch (IOException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
      return;
    }
    if (conn == null) {
      return;
    }

    conn.stop();
    connections.remove(conn.getUUID());
  }

  public String bluetoothGetLocalAddress() {
    return mBluetoothAdapter.getAddress();
  }

  public Boolean bluetoothDiscoveryStart() {
    return mBluetoothAdapter.startDiscovery();
  }

  public Boolean bluetoothDiscoveryCancel() {
    return mBluetoothAdapter.cancelDiscovery();
  }

  public Boolean bluetoothIsDiscovering() {
    return mBluetoothAdapter.isDiscovering();
  }

  @Override
  public void shutdown() {
    for (Map.Entry<String, BluetoothConnection> entry : connections.entrySet()) {
      entry.getValue().stop();
    }
    connections.clear();
  }
}

class BluetoothConnection {
  private BluetoothSocket mSocket;
  private BluetoothDevice mDevice;
  private OutputStream mOutputStream;
  private InputStream mInputStream;
  private BufferedReader mReader;
  private BluetoothServerSocket mServerSocket;
  private String UUID;

  public BluetoothConnection(BluetoothSocket mSocket) throws IOException {
    this(mSocket, null);
  }

  public BluetoothConnection(BluetoothSocket mSocket, BluetoothServerSocket mServerSocket)
      throws IOException {
    this.mSocket = mSocket;
    mOutputStream = mSocket.getOutputStream();
    mInputStream = mSocket.getInputStream();
    mDevice = mSocket.getRemoteDevice();
    mReader = new BufferedReader(new InputStreamReader(mInputStream, "ASCII"));
    this.mServerSocket = mServerSocket;
  }

  public void setUUID(String UUID) {
    this.UUID = UUID;
  }

  public String getUUID() {
    return UUID;
  }

  public String getRemoteBluetoothAddress() {
    return mDevice.getAddress();
  }

  public boolean isConnected() {
    if (mSocket == null) {
      return false;
    }
    try {
      mSocket.getRemoteDevice();
      mInputStream.available();
      mReader.ready();
      return true;
    } catch (Exception e) {
      return false;
    }
  }

  public void write(byte[] out) throws IOException {
    if (mOutputStream != null) {
      mOutputStream.write(out);
    } else {
      throw new IOException("Bluetooth not ready.");
    }
  }

  public void write(String out) throws IOException {
    this.write(out.getBytes());
  }

  public Boolean readReady() throws IOException {
    if (mReader != null) {
      return mReader.ready();
    }
    throw new IOException("Bluetooth not ready.");
  }

  public byte[] readBinary(int bufferSize) throws IOException {
    if (mReader != null) {
      byte[] buffer = new byte[bufferSize];
      int bytesRead = mInputStream.read(buffer);
      if (bytesRead == -1) {
        Log.e("Read failed.");
        throw new IOException("Read failed.");
      }
      byte[] truncatedBuffer = new byte[bytesRead];
      System.arraycopy(buffer, 0, truncatedBuffer, 0, bytesRead);
      return truncatedBuffer;
    }

    throw new IOException("Bluetooth not ready.");

  }

  public String read(int bufferSize) throws IOException {
    if (mReader != null) {
      char[] buffer = new char[bufferSize];
      int bytesRead = mReader.read(buffer);
      if (bytesRead == -1) {
        Log.e("Read failed.");
        throw new IOException("Read failed.");
      }
      return new String(buffer, 0, bytesRead);
    }
    throw new IOException("Bluetooth not ready.");
  }

  public String getConnectedDeviceName() {
    return mDevice.getName();
  }

  public void stop() {
    if (mSocket != null) {
      try {
        mSocket.close();
      } catch (IOException e) {
        Log.e(e);
      }
    }
    mSocket = null;
    if (mServerSocket != null) {
      try {
        mServerSocket.close();
      } catch (IOException e) {
        Log.e(e);
      }
    }
    mServerSocket = null;

    if (mInputStream != null) {
      try {
        mInputStream.close();
      } catch (IOException e) {
        Log.e(e);
      }
    }
    mInputStream = null;
    if (mOutputStream != null) {
      try {
        mOutputStream.close();
      } catch (IOException e) {
        Log.e(e);
      }
    }
    mOutputStream = null;
    if (mReader != null) {
      try {
        mReader.close();
      } catch (IOException e) {
        Log.e(e);
      }
    }
    mReader = null;
  }
}
