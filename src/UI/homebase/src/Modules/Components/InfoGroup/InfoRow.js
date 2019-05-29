import React from 'react';

const InfoRow = ({name, value}) => (
    <div className="info-group-box-items label-row">
        <div className="label-field">{name}</div>
        <div className="label-value truncate">{value}</div>
    </div>
);

export default InfoRow;