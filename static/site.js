function gotEmployees(data) {

  const detailForm = (event) => {
    event.preventDefault();
  };

  const submitButtonClick = (event) => {
    event.preventDefault();
    const leaveDate = document.getElementById('leave_date').value;
    const leaveReason = document.getElementById('leave_reason').value;

  if (!leaveDate || !leaveReason) {
    alert("Please fill in all fields.");
    return;
  }
  alert("Form submitted successfully!");

};
       
  const leaveForm = (
    <div>
      <h4>Add Leave Details</h4>
      <form id="leaveForm" onSubmit={detailForm}>
        <label for="leave_date">Leave Date</label>
        <input type="date" id="leave_date" name="leave_date"/><br/><br/>
        <label for="leave_reason">Leave Reason</label>
        <input type="text" id="leave_reason" name="leave_reason"/><br/><br/>
        <input className="leave-submit-btn" type="submit" value="Submit" onClick={submitButtonClick}/>
      </form>
    </div>
  );

  
  const employeeDetails = (
    <div>
      <h4> Details for <span className="emp-name">{data.fname} {data.lname}</span></h4>
      <h5> {data.title} </h5>
      <table>
        <tr>
          <th> First Name</th>
          <td> {data.fname}</td>
        </tr>
        <tr>
          <th> Last Name</th>
          <td> {data.lname}</td>
        </tr>
        <tr>
          <th> Email</th>
          <td> {data.email}</td>
        </tr>
        <tr>
          <th> Phone</th>
          <td> {data.phone}</td>
        </tr>
        <tr>
          <th> Leaves Taken</th>
          <td> {data.leave}</td>
        </tr>
        <tr>
          <th> Allowed Leaves</th>
          <td> {data.max_leaves}</td>
        </tr>
        <tr>
          <th>Remaining leaves</th>
          <td> {data.remaining_leaves}</td>
        </tr>
      </table>
      <br/><br/>
    </div>
  );


  const root = ReactDOM.createRoot(document.getElementById('root'));

  root.render(
    <div>
      {employeeDetails}
      {leaveForm}
    </div>
  );
}

$(function() {
    $("a.userlink").click(function(ev) {
    $.get(ev.target.href, gotEmployees);
    ev.preventDefault();
  });
});
