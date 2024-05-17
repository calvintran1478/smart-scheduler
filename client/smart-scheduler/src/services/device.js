export function getDeviceId() {
    let deviceId = localStorage.getItem('device_id');
    if (!deviceId) {
        deviceId = Math.floor(Math.random() * 1e16).toString();
        localStorage.setItem('device_id', deviceId);
    }
    return deviceId;
}