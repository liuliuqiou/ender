const crypto = require("crypto");

function parseVLESSHeader(buffer) {
    const version = buffer[0];
    const uuid = buffer.slice(1, 17).toString("hex");
    const command = buffer[17];
    const port = buffer.readUInt16BE(18);
    const addressType = buffer[20];

    let address;
    if (addressType === 1) {
        address = buffer.slice(21, 25).join(".");
    } else if (addressType === 2) {
        const len = buffer[21];
        address = buffer.slice(22, 22 + len).toString();
    } else {
        address = "::1";
    }

    return { version, uuid, command, port, address };
}

module.exports = { parseVLESSHeader };
