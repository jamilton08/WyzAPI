import axios from "axios";
import React from "react";

// reactstrap components
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  CardImg,
  CardTitle,
  FormGroup,
  Form,
  Input,
  InputGroupAddon,
  InputGroupText,
  InputGroup
} from "reactstrap";

// Core Components

function ResetCard1() {
  const [emailFocus, setEmailFocus] = React.useState("");
  const [emailFocus1, setEmailFocus1] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [passwordConfirm, setPasswordConfirm] = React.useState("");

  React.useEffect(() => {
    axios.get('http://127.0.0.1:8000/authentications/verify/token/'.concat(getToken(), "/"))
      .then((response) => {
        console.log(response);
      })
      .catch((error) => {

        if (error.response.status === 400){
        window.location.replace("http://localhost:3000/error")}
      }
    )
  })
  function getToken(){
    const url = window.location.href;
    const startIndex = url.lastIndexOf("/");
    return url.substring(startIndex + 1)
  }

  const handleSubmit = (e) => {
    axios.post("http://127.0.0.1:8000/authentications/verify/token/", {
      password : password,
      confirm_password : passwordConfirm
    })
    .then((response) => {
      console.log(response)
    })
    .catch((error) => {
      console.log(error)
    })
  }



  return (
    <>
      <Card className="bg-secondary shadow border-0">
        <CardHeader>
          <CardImg
            alt="..."
            src={require("assets/img/ill/bg5-1.svg").default}
          ></CardImg>
          <CardTitle className="text-center" tag="h4">
            Reset Password
          </CardTitle>
        </CardHeader>
        <CardBody className="px-lg-5 py-lg-5">
          <div className="text-center text-muted mb-4">
            <small>Enter email address to reset password</small>
          </div>
          <Form role="form">
            <FormGroup className={"mb-3 " + emailFocus}>
              <InputGroup className="input-group-alternative">
                <InputGroupAddon addonType="prepend">
                  <InputGroupText>
                    <i className="ni ni-key-25"></i>
                  </InputGroupText>
                </InputGroupAddon>
                <Input
                  placeholder="Password"
                  type="password"
                  onFocus={() => setEmailFocus("focused")}
                  onBlur={() => setEmailFocus("")}
                  onChange = {(e) => setPassword(e.target.value) }
                ></Input>
              </InputGroup>
            </FormGroup>
            <FormGroup className={"mb-3 " + emailFocus1}>
              <InputGroup className="input-group-alternative">
                <InputGroupAddon addonType="prepend">
                  <InputGroupText>
                    <i className="ni ni-lock-circle-open"></i>
                  </InputGroupText>
                </InputGroupAddon>
                <Input
                placeholder="Password"
                type="password"
                  onFocus={() => setEmailFocus1("focused")}
                  onBlur={() => setEmailFocus1("")}
                  onChange = {(e) => setPasswordConfirm(e.target.value)}
                ></Input>
              </InputGroup>

            </FormGroup>
            <div className="text-center">
              <Button className="my-4" color="primary" type="submit" onClick={handleSubmit}>
                Send
              </Button>
            </div>
          </Form>
        </CardBody>
      </Card>
    </>
  );
}

export default ResetCard1;
