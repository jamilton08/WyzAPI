import React from "react";

// reactstrap components
// import {
//
// } from "reactstrap";

// Core Components
import DemoNavbar from "components/navbars/DemoNavbar.js";
import DemoFooter from "components/footers/DemoFooter.js";

import Header4 from "components/headers/Header4.js";
import Feature4 from "components/features/Feature4.js";
import Blogs1 from "components/blogs/Blogs1.js";
import Team1 from "components/teams/Team1.js";
import Projects2 from "components/projects/Projects2.js";
import ContactUs3 from "components/contact-us/ContactUs3.js";
import Table2 from "components/tables/Table2.js";
import Accordion1 from "components/accordions/Accordion1.js";



function Home() {
  React.useEffect(() => {
    document.body.classList.add("sections-page");
    window.scrollTo(0, 0);
    document.body.scrollTop = 0;
    var href = window.location.href.substring(
      window.location.href.lastIndexOf("#") + 1
    );
    if (
      window.location.href.lastIndexOf("#") > 0 &&
      document.getElementById(href)
    ) {
      document.getElementById(href).scrollIntoView();
    }
    return function cleanup() {
      document.body.classList.remove("sections-page");
    };
  });
  return (
    <>
      <DemoNavbar type="dark" />
      <div className="wrapper">
        <Header4 />
        <Feature4 />
        <Blogs1 />
        <Team1 />
        <Projects2 />
        <ContactUs3 />
        <Table2 />
        <Accordion1 />
        <DemoFooter />
      </div>
    </>
  );
}

export default Home;
