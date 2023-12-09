function gotEmployees(data) {
  console.log(data);
//   $("span.info")[0].innerHTML = "Loaded";
  $("#userdetails")[0].innerHTML = `
      <h4> Details for ${data.fname} ${data.lname}</h4>
      <h5> ${data.title} </h5>
      <table>
          <tr>
              <th> First Name </th>
              <td> ${data.fname}</td>
          </tr>
          <tr>
              <th> Last Name </th>
              <td> ${data.lname}</td>
          </tr>
          <tr>
              <th> Email </th>
              <td> ${data.email}</td>
          </tr>
          <tr>
              <th> Phone </th>
              <td> ${data.phone}</td>
          </tr>
          <tr>
              <th> Leaves Taken  </th>
              <td> ${data.leave}</td>
          </tr>
          <tr>
              <th> Allowed Leaves  </th>
              <td> ${data.max_leaves}</td>
          </tr>
          <tr>
              <th>Remaining leaves </th>
              <td> ${ data.remaining_leaves }</td>
          </tr>

      </table>
      <br><br>
    <h4>Add Leave Details</h4>

    <form method="post" action="/add_leave/${data.id}">
      <label for="leave_date">Leave Date</label>
      <input type="date" id="leave_date" name="leave_date"><br><br>
      <label for="leave_reason">Leave Reason</label>
      <input type="text" id="leave_reason" name="leave_reason"><br><br>
      <input type="submit" value="Submit">
    </form>

  `;
}

$(function() {
  $("a.userlink").click(function(ev) {
    //   $("span.info")[0].innerHTML = "Loading...";
      $.get(ev.target.href, gotEmployees);
      ev.preventDefault();
  });
});


