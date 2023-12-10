function gotEmployees(data) {
  console.log(data);
  //   $("span.info")[0].innerHTML = "Loaded";
  $("#userdetails")[0].innerHTML = `
      <h4> Details for <span class="emp-name">${data.fname} ${data.lname}</span></h4>
      <h5> ${data.title} </h5>
      <table>
          <tr>
              <th> First Name &nbsp&nbsp</th>
              <td> ${data.fname}</td>
          </tr>
          <tr>
              <th> Last Name &nbsp&nbsp</th>
              <td> ${data.lname}</td>
          </tr>
          <tr>
              <th> Email &nbsp&nbsp</th>
              <td> ${data.email}</td>
          </tr>
          <tr>
              <th> Phone &nbsp&nbsp</th>
              <td> ${data.phone}</td>
          </tr>
          <tr>
              <th> Leaves Taken  &nbsp&nbsp</th>
              <td> ${data.leave}</td>
          </tr>
          <tr>
              <th> Allowed Leaves &nbsp &nbsp</th>
              <td> ${data.max_leaves}</td>
          </tr>
          <tr>
              <th>Remaining leaves &nbsp&nbsp</th>
              <td> ${data.remaining_leaves}</td>
          </tr>

      </table>
      <br><br>
      <div>
    <button class="leave-btn" >Add Leave</button>
<div class="form-container">
    <form id="leaveForm" method="post"  action="/add_leave/${data.id}">
      <label for="leave_date">Leave Date</label>
      <input type="date" id="leave_date" name="leave_date"><br><br>
      <label for="leave_reason">Leave Reason</label>
      <input type="text" id="leave_reason" name="leave_reason"><br><br>
      <input class="leave-submit-btn" type="submit" value="Submit">
    </form>
    </div>
</div>
  `;

  
  $(".leave-btn").click(function (ev) {
    $(".form-container").addClass("visible");
    ev.preventDefault(); 
  });
}

$(function() {
  $("a.userlink").click(function(ev) {
    $.get(ev.target.href, gotEmployees);
    ev.preventDefault();
  });
});

$(document).on("submit", "#leaveForm", function (event) {
    event.preventDefault();
    var leaveDate = $("#leave_date").val();
    var leaveReason = $("#leave_reason").val();

    if (!leaveDate || !leaveReason) {
      alert("Please fill in all fields.");
      return;
    }
    var formData = $(this).serialize();

    $.ajax({
      type: "POST",
      url: $(this).attr("action"),
      data: formData,
      success: function (response) {
        console.log(response.body);
        $("#leave_date").val("");
        $("#leave_reason").val("");
        alert("Form submitted successfully");

      },
      error: function (error) {
        console.log(error);
        alert("Error submitting form", error);
      }
    });
  })

