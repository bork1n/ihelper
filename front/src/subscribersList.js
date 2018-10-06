import React from 'react';
import ReactDOM from 'react-dom';
import { timeConverter, getInfoById } from './App';
import ReactTable from "react-table";
import 'react-table/react-table.css';
import { CSVLink, CSVDownload } from 'react-csv';


const columns = [
  {
    Header: "Img",
    accessor: "profile_pic_url",
    width: 70,
    Cell: row => (
      <a href={'https://instagram.com/' + row.original.username}><img src={row.row.profile_pic_url} width="50px" /></a>

    )
  },

  {
    Header: "username",
    accessor: "username",
    Cell: row => (
      <span>
        <a href={'https://instagram.com/' + row.original.username}>{row.value}</a>
        <br />
        {row.original.full_name}
      </span>

    )
  },
  {
    Header: "followed_by",
    accessor: "edge_followed_by.count",
    width: 100,
    filterMethod: (filter, row) => row._original.edge_followed_by.count >= filter.value
  },
  {
    Header: "follow",
    accessor: "edge_follow.count",
    width: 100,
    filterMethod: (filter, row) => row._original.edge_follow.count >= filter.value
  },
  {
    Header: "history",
    Cell: (row) => {
      var history = row.original.ihelper_user_history;
      var text_history = history.map(function(h, index) {
        var dt = timeConverter(h.ts);
        return <li key={index}>
          <span style={{ color: h.val.action == 1 ? 'green' : 'red' }}>
            {dt} {getInfoById(h.val.producer)['username']}
          </span>
        </li>;
      })

      return <ul>
        {text_history}
      </ul>
    },
    filterMethod: (filter, row) => {
      var history = row._original.ihelper_user_history;
      return history.some((h) => getInfoById(h.val.producer)['username'].indexOf(filter.value) !== -1)
    }
  }
];




class FollowersTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      sortedData: null,

    };
  }

  download = () => {
    this.csvdata = this.dataTable.getResolvedState().sortedData.map((h)=> {
        var line = {};
        line.username = h.username
        return line;
      });

    this.setState(
      { boolean: true },
      () => { this.setState({ boolean: false }) }
    )
  }

  render() {
    if (!this.props.followers) {
      return <table><tbody><tr><td>No {this.props.header}</td></tr></tbody></table>
    }


    return (
      <div>
        <h3>{this.props.header} <button onClick={this.download}>download as .csv</button></h3>
        <ReactTable
          ref={(ref) => this.dataTable = ref}
          data={this.props.followers}
          columns={columns}
          defaultPageSize={Number(this.props.size)}
          filterable
          className="-striped -highlight"
        />
        {this.state.boolean ? <CSVDownload target="_parent" data={this.csvdata}></CSVDownload> : ''}

      </div>
    )
  }
}

class SubsribersList extends React.Component {



  render() {
    if (!this.props.followers || !this.props.followers.hasOwnProperty('created')) {
      return (
        <table></table>
      )
    }

    const followers = this.props.followers;

    const deleted = followers.deleted ? followers.deleted.length : 0;
    const added = followers.created ? followers.created.length : 0;
    return (
      <div>
        <p>{deleted} deleted, {added} added, {added - deleted} total</p>
        <div style={{ width: '60%' }}>
          <FollowersTable header="Lost Followers" followers={followers.deleted} color="#aa0000" size="10" />
        </div>
        <div style={{ width: '60%' }}>
          <FollowersTable header="New Followers" followers={followers.created} color="#00aa00" size="10" />
        </div>
      </div>
    )
  }

}

export default SubsribersList;
